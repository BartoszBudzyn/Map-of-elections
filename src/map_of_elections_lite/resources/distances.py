from collections.abc import Callable
from enum import Enum
from typing import Any, Union

import mapof.elections.distances.main_approval_distances as app_dist
import mapof.elections.distances.main_ordinal_distances as ord_dist
from mapof.elections.objects import Election

class Distance(Enum):
    """
    An enum of election distances (i.e. ways of measuring distances between elections).

    Attributes:
        distance_id: an ID as defined in the original mapof-elections
        implementation: A mapof function that calculates a given distance.
    """
    def __init__(self, distance_id: str, implementation: Callable[[Election, Election, Callable[..., Any]], Union[float, list]]):
        self.distance_id = distance_id
        self.implementation = implementation

class OrdinalDistance(Distance):
    """An enum of distances for ordinal elections."""
    EMD_POSITIONWISE = ("emd-positionwise", ord_dist.positionwise_distance)
    L1_POSITIONWISE = ("l1-positionwise", ord_dist.positionwise_distance)
    EMD_BORDAWISE = ("emd-bordawise", ord_dist.bordawise_distance)
    L1_PAIRWISE = ("l1-pairwise", ord_dist.pairwise_distance)
    MAXIMUM_COMMON_VOTER_SUBELECTION = ("maximum_common_voter_subelection", ord_dist.maximum_common_voter_subelection)
    BLANK_DISTANCE = ("blank_distance", ord_dist.blank_distance)
    SPEARMAN_AA = ("spearman_aa", ord_dist.spearman_distance_fastmap)
    SWAP = ("swap", ord_dist.swap_distance)
    # Maximum common voter subelection wasn't implemented in mapof

class ApprovalDistances(Distance):
    """An enum of distances for approval elections."""
    L1_APPROVALWISE = ("l1-approvalwise", app_dist.approvalwise_distance)
