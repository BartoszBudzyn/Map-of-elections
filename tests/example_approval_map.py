import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from map_of_elections_lite.exports.json_exporter import enable_json_export_backend
from map_of_elections_lite.exports.json_exporter import export_experiment_snapshot_json, prepare_json_approval_experiment
from map_of_elections_lite.exports import proto_exporter
from map_of_elections_lite.resources.cultures import ApprovalCulture
from map_of_elections_lite.resources.distances import ApprovalDistances


def create_simple_approval_json_map():
    target_dir = _SRC_DIR / "map_of_elections_lite"
    enable_json_export_backend(output_dir=str(target_dir))

    experiment = prepare_json_approval_experiment(experiment_id="test_approval_map")

    experiment.add_family(
        culture_id=ApprovalCulture.IMPARTIAL.culture_id,
        size=5,
        num_candidates=8,
        num_voters=100,
        params={'p': 0.5},
        color='green',
        marker='x',
        label='Impartial Culture (p=0.5)'
    )

    experiment.add_family(
        culture_id=ApprovalCulture.RESAMPLING.culture_id,
        size=5,
        num_candidates=8,
        num_voters=100,
        params={'p': 0.5, 'phi': 0.5},
        color='blue',
        marker='o',
        label='Resampling (p=0.5, phi=0.5)'
    )

    experiment.compute_distances(
        distance_id=ApprovalDistances.L1_APPROVALWISE.distance_id
    )
    experiment.embed_2d(embedding_id='fr')

    # Approval votes are sets ({a, d}) — they are serialised as sorted lists
    # in both JSON and protobuf so the file structure is identical to the
    # ordinal case. The Vote.candidate_order field (proto) / votes array
    # (JSON) carries the sorted list of approved candidate indices.
    json_path = str(target_dir / "test_approval_json_output.json")
    output_path = export_experiment_snapshot_json(
        experiment,
        output_path=json_path
    )
    print(f"JSON saved as: {output_path}")

    proto_path = str(target_dir / "test_approval_proto_output.pb")
    proto_out = proto_exporter.export_experiment_snapshot_proto(experiment, output_path=proto_path)
    print(f"Proto saved as: {proto_out}")

    return experiment


if __name__ == '__main__':

    experiment = create_simple_approval_json_map()
