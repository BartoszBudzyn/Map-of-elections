"""Minimal legacy example: create an offline experiment with the old folder-based workflow."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import mapof.elections as mapof

from map_of_elections_lite.resources.cultures import OrdinalCulture
from map_of_elections_lite.resources.distances import OrdinalDistance


def create_legacy_offline_experiment() -> None:
    experiment = mapof.prepare_offline_ordinal_experiment(
        experiment_id="legacy_map_check"
    )

    experiment.add_family(
        culture_id=OrdinalCulture.IMPARTIAL.culture_id,
        size=3,
        num_candidates=6,
        num_voters=20,
        color="green",
        marker="x",
        label="IC",
    )

    experiment.add_family(
        culture_id=OrdinalCulture.MALLOWS.culture_id,
        size=3,
        num_candidates=6,
        num_voters=20,
        params={"phi": 0.5},
        color="blue",
        marker="o",
        label="Mallows",
    )

    experiment.prepare_elections()
    experiment.compute_distances(distance_id=OrdinalDistance.EMD_POSITIONWISE.distance_id)
    experiment.embed_2d(embedding_id="fr")
    experiment.print_map_2d(title="Legacy offline map", saveas="legacy_map_check")

    print("Created offline experiment: experiments/legacy_map_check/")


if __name__ == "__main__":
    create_legacy_offline_experiment()
