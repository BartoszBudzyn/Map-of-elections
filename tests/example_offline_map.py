from map_of_elections_lite.exports.json_exporter import enable_json_export_backend
from map_of_elections_lite.exports.json_exporter import export_experiment_snapshot_json, prepare_json_ordinal_experiment
from map_of_elections_lite.exports import proto_exporter
from map_of_elections_lite.resources.cultures import OrdinalCulture
from map_of_elections_lite.resources.distances import OrdinalDistance


def create_simple_json_map():

    enable_json_export_backend(output_dir="../src/map_of_elections_lite")

    experiment = prepare_json_ordinal_experiment(experiment_id="test_map")

    experiment.add_family(
        culture_id=OrdinalCulture.IMPARTIAL.culture_id,
        size=5,
        num_candidates=8,
        num_voters=100,
        color='green',
        marker='x',
        label='Impartial Culture (IC)'
    )

    experiment.add_family(
        culture_id=OrdinalCulture.MALLOWS.culture_id,
        size=5,
        num_candidates=8,
        num_voters=100,
        params={'phi': 0.5},
        color='blue',
        marker='o',
        label='Mallows (phi=0.5)'
    )

    experiment.compute_distances(
        distance_id=OrdinalDistance.EMD_POSITIONWISE.distance_id
    )
    experiment.embed_2d(embedding_id='fr')

    output_path = export_experiment_snapshot_json(experiment, output_path="../src/map_of_elections_lite/test_json_output.json")
    print(f"JSON saved as: {output_path}")

    proto_path = "../src/map_of_elections_lite/test_proto_output.pb"
    proto_out = proto_exporter.export_experiment_snapshot_proto(experiment, output_path=proto_path)
    print(f"Proto saved as: {proto_out}")

    return experiment


if __name__ == '__main__':

    experiment = create_simple_json_map()
