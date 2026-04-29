import json
import importlib
import os
import re
from collections import Counter
from copy import deepcopy
from typing import Any

from bson import BSON
from mapof.elections import OrdinalElectionExperiment

_OUTPUT_DIR = "."
_EXPORT_FORMAT = "json" # Default export format


def _experiment_path(experiment, output_dir: str | None = None) -> str:
    base_dir = _OUTPUT_DIR if output_dir is None else output_dir
    filename = f"{experiment.experiment_id}.{_EXPORT_FORMAT}" # Use global _EXPORT_FORMAT

    if base_dir in ("", "."):
        return filename

    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)


def _make_base_document(experiment) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "experiment_id": experiment.experiment_id,
        "distance_id": getattr(experiment, "distance_id", None),
        "embedding_id": getattr(experiment, "embedding_id", None),
        "instances": {},
        "distances": {},
        "distance_times": {},
        "coordinates": {},
        "features": {},
        "normalized_features": {},
        "distance_chunks": {},
    }


def _load_document(path: str, experiment) -> dict[str, Any]:
    if not os.path.exists(path):
        return _make_base_document(experiment)

    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif path.endswith(".bson"):
        with open(path, "rb") as f:
            return BSON.decode(f.read())
    return _make_base_document(experiment)


def _save_document(path: str, document: dict[str, Any]) -> None:
    if path.endswith(".json"):
        fmt = "json"
    elif path.endswith(".bson"):
        fmt = "bson"
    else:
        fmt = _EXPORT_FORMAT

    if fmt == "json":
        raw_json = json.dumps(document, ensure_ascii=False, indent=2)

        pattern = r'\[\s*((?:\-?\d+(?:\.\d+)?,\s*)*\-?\d+(?:\.\d+)?)\s*\]'
        def repl(m):
            elements = [x.strip() for x in m.group(1).split(',')]
            return '[' + ', '.join(elements) + ']'
        
        compact_json = re.sub(pattern, repl, raw_json)
    
        with open(path, "w", encoding="utf-8") as f:
            f.write(compact_json)
    elif fmt == "bson":
        with open(path, "wb") as f:
            f.write(BSON.encode(document))



def _to_serializable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]

    if isinstance(value, set):
        return sorted(_to_serializable(v) for v in value)

    if hasattr(value, "tolist"):
        return _to_serializable(value.tolist())

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def _upsert_experiment_header(document: dict[str, Any], experiment) -> None:
    document["schema_version"] = document.get("schema_version", "1.0")
    document["experiment_id"] = experiment.experiment_id
    document["distance_id"] = getattr(experiment, "distance_id", document.get("distance_id"))
    document["embedding_id"] = getattr(experiment, "embedding_id", document.get("embedding_id"))

def _aggregate_votes(votes: list[list[int]]) -> list[tuple[tuple[int, ...], int]]:
    votes = [tuple(i) for i in votes]
    return Counter(votes).most_common(None)

def prepare_json_ordinal_experiment(experiment_id: str = "experiment", **kwargs) -> OrdinalElectionExperiment:
    import mapof.elections as mapof

    experiment = mapof.prepare_online_ordinal_experiment(**kwargs)
    experiment.experiment_id = experiment_id
    return experiment


def export_feature_to_file(
    experiment,
    feature_id: str,
    feature_dict: dict | None = None,
    saveas: str | None = None,
) -> None:
    path = _experiment_path(experiment)
    document = _load_document(path, experiment)
    _upsert_experiment_header(document, experiment)

    key = saveas or feature_id
    document["features"][key] = {
        "feature_id": feature_id,
        "values": _to_serializable(feature_dict or {}),
    }

    _save_document(path, document)


def export_normalized_feature_to_file(
    experiment,
    feature_dict: dict | None = None,
    saveas: str | None = None,
) -> None:
    path = _experiment_path(experiment)
    document = _load_document(path, experiment)
    _upsert_experiment_header(document, experiment)

    key = saveas or "normalized"
    document["normalized_features"][key] = _to_serializable(feature_dict or {})

    _save_document(path, document)


def export_embedding_to_file(
    experiment,
    embedding_id: str,
    saveas: str | None,
    dim: int,
    my_pos,
) -> None:
    path = _experiment_path(experiment)
    document = _load_document(path, experiment)
    _upsert_experiment_header(document, experiment)

    key = saveas or f"{embedding_id}_{getattr(experiment, 'distance_id', 'unknown')}_{dim}d"

    coordinates: dict[str, list[float]] = {}
    ctr = 0
    for instance_id in experiment.instances:
        x = round(experiment.coordinates[instance_id][0], 5)
        if dim == 1:
            coordinates[instance_id] = [x]
        else:
            y = round(experiment.coordinates[instance_id][1], 5)
            if dim == 2:
                coordinates[instance_id] = [x, y]
            else:
                z = round(my_pos[ctr][2], 5)
                coordinates[instance_id] = [x, y, z]
        ctr += 1

    document["coordinates"][key] = {
        "embedding_id": embedding_id,
        "dim": dim,
        "values": coordinates,
    }

    _save_document(path, document)


def export_distances_to_file(
    experiment,
    distance_id: str,
    distances: dict[str, dict[str, float]],
    times: dict[str, dict[str, float]],
    ids=None,
) -> None:
    path = _experiment_path(experiment)
    document = _load_document(path, experiment)
    _upsert_experiment_header(document, experiment)

    distance_values: dict[str, float] = {}
    time_values: dict[str, float] = {}

    for pair in ids or []:
        instance_1, instance_2 = pair
        pair_key = f"{instance_1}|{instance_2}"
        distance_values[pair_key] = float(distances[instance_1][instance_2])
        time_values[pair_key] = float(times[instance_1][instance_2])

    document["distances"][distance_id] = distance_values
    document["distance_times"][distance_id] = time_values

    _save_document(path, document)


def export_distances_multiple_processes(
    experiment,
    instances_ids,
    distances,
    times,
    process_id,
) -> None:
    path = _experiment_path(experiment)
    document = _load_document(path, experiment)
    _upsert_experiment_header(document, experiment)

    key = f"{getattr(experiment, 'distance_id', 'distance')}_p{process_id}"
    chunk = {}
    for election_id_1, election_id_2 in instances_ids:
        pair_key = f"{election_id_1}|{election_id_2}"
        chunk[pair_key] = {
            "distance": float(distances[election_id_1][election_id_2]),
            "time": float(times[election_id_1][election_id_2]),
        }

    document["distance_chunks"][key] = chunk
    _save_document(path, document)


def export_experiment_snapshot(
    experiment,
    output_path: str | None = None,
    include_votes: bool = True,
) -> str:
    """
    Export full in-memory experiment state to a single file (JSON or BSON).

    Parameters
    ----------
    experiment:
        A mapof experiment object.
    output_path:
        Optional custom output path. If omitted, uses experiments/<experiment_id>.<format>.
    include_votes:
        Whether to include raw votes for every instance.

    Returns
    -------
    str
        Path to the created file.
    """
    path = output_path or _experiment_path(experiment)
    document = _load_document(path, experiment)
    _upsert_experiment_header(document, experiment)

    instances_dump = {}
    for instance_id, instance in getattr(experiment, "instances", {}).items():
        entry = {
            "instance_id": instance_id,
            "culture_id": getattr(instance, "culture_id", None),
            "num_candidates": getattr(instance, "num_candidates", None),
            "num_voters": getattr(instance, "num_voters", None),
            "params": _to_serializable(getattr(instance, "params", {})),
        }
        if include_votes and hasattr(instance, "votes"):
            entry["votes"] = _to_serializable(_aggregate_votes(instance.votes))

        instances_dump[instance_id] = entry

    document["instances"] = instances_dump
    document["distances"] = _to_serializable(deepcopy(getattr(experiment, "distances", {})))
    document["distance_times"] = _to_serializable(deepcopy(getattr(experiment, "times", {})))
    document["coordinates"] = _to_serializable(deepcopy(getattr(experiment, "coordinates", {})))
    document["features"] = _to_serializable(deepcopy(getattr(experiment, "features", {})))

    _save_document(path, document)
    return path


def enable_export_backend(output_dir: str = "experiments", fmt: str = "json") -> None:
    """
    Patch mapof exporters so mapof writes to the specified format (JSON or BSON).

    After calling this once, operations such as:
    - experiment.compute_distances(...)
    - experiment.embed_2d(...)
    - experiment.compute_feature(...)
    will persist into one file per experiment in the chosen format.

    Parameters
    ----------
    output_dir:
        The directory where export files will be saved.
    fmt:
        The export format, either "json" or "bson".

    Notes
    -----
    - Use together with prepare_json_ordinal_experiment() for a fully configured flow.
    """
    global _OUTPUT_DIR, _EXPORT_FORMAT
    _OUTPUT_DIR = output_dir
    _EXPORT_FORMAT = fmt

    module_names = [
        "mapof.core.persistence.experiment_exports",
        "mapof.elections.persistence.experiment_exports",
    ]

    for module_name in module_names:
        try:
            exp_exports = importlib.import_module(module_name)
            exp_exports.export_feature_to_file = export_feature_to_file
            exp_exports.export_normalized_feature_to_file = export_normalized_feature_to_file
            exp_exports.export_embedding_to_file = export_embedding_to_file
            exp_exports.export_distances_to_file = export_distances_to_file
            exp_exports.export_distances_multiple_processes = export_distances_multiple_processes
            exp_exports.export_experiment_snapshot = export_experiment_snapshot
        except ModuleNotFoundError:
            continue

def enable_json_export_backend(output_dir: str="experiments"): enable_export_backend(output_dir, "json")
def enable_bson_export_backend(output_dir: str="experiments"): enable_export_backend(output_dir, "bson")
