from mapof.elections.objects.ElectionExperiment import ElectionExperiment

from .json_exporter import _aggregate_votes
from . import elections_pb2, Instance


def serialize_experiment(experiment: ElectionExperiment, include_votes: bool) -> elections_pb2.Experiment:
    """
    Returns the experiment serialized to a ProtoBuf format.
    :param include_votes: indicates whether we should include votes in the generated protobuf object
    :param experiment: election experiment as defined in Mapof-elections.
    :return: serialized experiment.
    """
    proto_experiment = elections_pb2.Experiment()
    proto_experiment.experiment_id = experiment.experiment_id or ""
    proto_experiment.distance_id = experiment.distance_id or ""
    proto_experiment.embedding_id = experiment.embedding_id or ""

    distances = experiment.distances or {}
    coordinates = experiment.coordinates or {}
    for instance_id, instance in experiment.instances.items():
        entry = elections_pb2.Instance()

        entry.instance_id = instance.instance_id or instance_id
        entry.culture_id = instance.culture_id or ""
        entry.num_candidates = instance.num_candidates or 0
        entry.num_voters = instance.num_voters or 0

        for param_key, param_value in (instance.params or {}).items():
            entry.params[param_key] = str(param_value)

        if include_votes and hasattr(instance, "votes"):
            votes_aggregated = _aggregate_votes(instance.votes)
            for order, cardinality in votes_aggregated:
                vote = elections_pb2.Vote()
                vote.candidate_order.extend(list(order))
                vote.cardinality = cardinality
                entry.votes.append(vote)

        if entry.instance_id in distances:
            for election_name, distance in distances[entry.instance_id].items():
                entry.distances[election_name] = distance

        if entry.instance_id in coordinates:
            entry.x_coord = coordinates[entry.instance_id][0]
            entry.y_coord = coordinates[entry.instance_id][1]

        proto_experiment.instances[instance_id].CopyFrom(entry)

    return proto_experiment


def export_experiment_snapshot_proto(
    experiment: ElectionExperiment,
    output_path: str | None = None,
    include_votes: bool = True,
) -> str:
    """
    Export full in-memory experiment state to a single ProtoBuf file.
    :param experiment: A mapof experiment object.
    :param output_path: Optional custom output path. If omitted, uses experiments/<experiment_id>.pb.
    :param include_votes: Whether to include raw votes for every instance.
    :return: Path to the created ProtoBuf file.
    """
    path = output_path or f"experiments/{getattr(experiment, 'experiment_id', 'experiment')}.pb"
    proto_experiment = serialize_experiment(experiment, include_votes)
    with open(path, "wb") as f:
        f.write(proto_experiment.SerializeToString())
    return path
