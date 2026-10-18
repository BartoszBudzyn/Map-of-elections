from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from mapof.core.persistence.experiment_imports import (
    add_coordinates_to_experiment,
    add_distances_to_experiment,
)
from mapof.elections.persistence.election_imports import import_ordinal_election

from . import proto_exporter


def _read_feature(path: Path) -> dict[str, dict[str, float | str | None]]:
    values: dict[str, dict[str, float | str | None]] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source, delimiter=";")
        if not reader.fieldnames:
            raise ValueError(f"Feature file has no header: {path}")
        id_column = "instance_id" if "instance_id" in reader.fieldnames else "election_id"
        columns = [column for column in reader.fieldnames if column != id_column]
        for row in reader:
            instance_id = row[id_column]
            for column in columns:
                raw = row[column]
                if raw in {"", "None", "Blank", "''", '""'}:
                    value: float | str | None = None
                else:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = raw
                values.setdefault(column, {})[instance_id] = value
    return values


def _read_coordinate_dimension(path: Path) -> int:
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        fields = csv.DictReader(source, delimiter=";").fieldnames or []
    dimensions = [axis for axis in ("x", "y", "z") if axis in fields]
    if not dimensions or dimensions != ["x", "y", "z"][: len(dimensions)]:
        raise ValueError(f"Unsupported coordinate columns in {path}: {fields}")
    return len(dimensions)


def _instance_ids(experiment_dir: Path) -> set[str]:
    ids: set[str] = set()
    for folder, suffixes in (
        ("coordinates", (".csv",)),
        ("features", (".csv",)),
        ("distances", (".csv",)),
    ):
        directory = experiment_dir / folder
        for path in directory.glob("*.csv") if directory.is_dir() else ():
            with path.open("r", newline="", encoding="utf-8-sig") as source:
                reader = csv.DictReader(source, delimiter=";")
                fields = reader.fieldnames or []
                id_column = (
                    "instance_id"
                    if "instance_id" in fields
                    else "election_id"
                    if "election_id" in fields
                    else None
                )
                if id_column:
                    for row in reader:
                        if row[id_column]:
                            ids.add(row[id_column])
    return ids


def _read_legacy_instances(
    root: Path, experiment_id: str, instance_ids: set[str]
) -> dict[str, SimpleNamespace]:
    """Read election metadata and votes when the legacy .soc files exist."""
    instances: dict[str, SimpleNamespace] = {}
    with _working_directory(root):
        for instance_id in sorted(instance_ids):
            path = Path("experiments") / experiment_id / "elections" / f"{instance_id}.soc"
            if not path.exists():
                instances[instance_id] = SimpleNamespace(instance_id=instance_id)
                continue
            (
                votes,
                num_voters,
                num_candidates,
                params,
                culture_id,
                _alliances,
                _num_distinct_votes,
                _quantities,
                _distinct_votes,
            ) = import_ordinal_election(
                experiment_id=experiment_id,
                election_id=instance_id,
                is_shifted=False,
            )
            instances[instance_id] = SimpleNamespace(
                instance_id=instance_id,
                culture_id=culture_id.strip() if culture_id else culture_id,
                num_candidates=num_candidates,
                num_voters=num_voters,
                params=params or {},
                votes=votes.tolist(),
            )
    return instances


def convert_legacy_results(
    legacy_experiment_dir: str | os.PathLike[str],
    json_output_path: str | os.PathLike[str],
    proto_output_path: str | os.PathLike[str],
    experiment_id: str | None = None,
) -> tuple[str, str]:
    """Convert ``experiments/<id>/{distances,features,coordinates}``.

    Existing mapof import functions are used for distances and coordinates.
    Feature columns are copied without filtering; missing values become JSON
    null.  The JSON output is the complete result format.  The protobuf output
    uses only the fields already present in its schema.
    """
    directory = Path(legacy_experiment_dir).resolve()
    experiment_id = experiment_id or directory.name
    root = directory.parent.parent
    instance_ids = _instance_ids(directory)
    if not instance_ids:
        raise FileNotFoundError(f"No result rows found in {directory}")

    distances: dict[str, dict[str, float]] = {}
    times: dict[str, dict[str, float]] = {}
    distance_sets: dict[str, dict[str, float]] = {}
    time_sets: dict[str, dict[str, float]] = {}
    distance_id = None
    distance_dir = directory / "distances"
    for path in sorted(distance_dir.glob("*.csv")) if distance_dir.is_dir() else ():
        distance_id = distance_id or path.stem
        with _working_directory(root):
            loaded_distances, loaded_times, _stds, _mappings = (
                add_distances_to_experiment(experiment_id, path.stem, sorted(instance_ids))
            )
        distance_sets[path.stem] = {}
        time_sets[path.stem] = {}
        for first, row in loaded_distances.items():
            for second, value in row.items():
                distances.setdefault(first, {})[second] = value
                distance_sets[path.stem][f"{first}|{second}"] = value
        for first, row in loaded_times.items():
            for second, value in row.items():
                times.setdefault(first, {})[second] = value
                time_sets[path.stem][f"{first}|{second}"] = value

    coordinates: dict[str, dict[str, object]] = {}
    embedding_id = None
    coordinate_dir = directory / "coordinates"
    for path in sorted(coordinate_dir.glob("*.csv")) if coordinate_dir.is_dir() else ():
        match = re.match(r"(?P<embedding>.+)_(?P<distance>.+)_(?P<dim>\d+)d$", path.stem)
        embedding_id = embedding_id or (match.group("embedding") if match else path.stem)
        dimension = _read_coordinate_dimension(path)
        with _working_directory(root):
            values = add_coordinates_to_experiment(
                experiment_id, "", "", sorted(instance_ids), dimension, path.name
            )
        coordinates[path.stem] = {
            "embedding_id": path.stem,
            "dim": dimension,
            "values": values,
        }

    features: dict[str, object] = {}
    feature_dir = directory / "features"
    for path in sorted(feature_dir.glob("*.csv")) if feature_dir.is_dir() else ():
        features[path.stem] = {"feature_id": path.stem, "values": _read_feature(path)}

    instances = _read_legacy_instances(root, experiment_id, instance_ids)
    document = {
        "experiment_id": experiment_id,
        "distance_id": distance_id,
        "embedding_id": embedding_id,
        "instances": {},
        "distances": distance_sets,
        "distance_times": time_sets,
        "coordinates": coordinates,
        "features": features,
        "normalized_features": {},
        "distance_chunks": {},
        "legacy_instance_distances": distances,
        "legacy_instance_times": times,
    }
    for instance_id in sorted(instance_ids):
        instance = instances[instance_id]
        entry = {"instance_id": instance_id}
        for field in ("culture_id", "num_candidates", "num_voters", "params"):
            if hasattr(instance, field):
                entry[field] = getattr(instance, field)
        if hasattr(instance, "votes"):
            entry["votes"] = [
                [list(order), cardinality]
                for order, cardinality in Counter(map(tuple, instance.votes)).most_common()
            ]
        document["instances"][instance_id] = entry
    json_path = Path(json_output_path)
    proto_path = Path(proto_output_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    proto_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as target:
        json.dump(document, target, ensure_ascii=False, indent=2, allow_nan=False)

    selected_coordinates = next(
        (item["values"] for item in coordinates.values()), {}
    )
    experiment = SimpleNamespace(
        experiment_id=experiment_id,
        distance_id=distance_id or "",
        embedding_id=embedding_id or "",
        instances=instances,
        distances=distances,
        times=times,
        coordinates=selected_coordinates,
        features={},
    )
    proto_exporter.export_experiment_snapshot_proto(experiment, str(proto_path), include_votes=False)
    return str(json_path), str(proto_path)


class _working_directory:
    def __init__(self, path: Path):
        self.path = path
        self.previous: Path | None = None

    def __enter__(self):
        self.previous = Path.cwd()
        os.chdir(self.path)

    def __exit__(self, *_):
        os.chdir(self.previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_experiment_dir", type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--proto", required=True, type=Path)
    parser.add_argument("--experiment-id")
    args = parser.parse_args()
    print(convert_legacy_results(args.legacy_experiment_dir, args.json, args.proto, args.experiment_id))


if __name__ == "__main__":
    main()
