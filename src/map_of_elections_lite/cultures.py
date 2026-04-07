from abc import ABC
from collections.abc import Callable
from enum import Enum
from typing import Any

import prefsampling.approval as psa

import mapof.elections.cultures.prefsampling_mask as masks

class Culture(Enum, ABC):
    """
    Base class for all cultures (i.e. ways of sampling elections).
    :param culture_id: an ID as defined in the original mapof-elections
    :param implementation: PrefSampling sampling function
    :param implementation_mask: mapof-elections mask for the PrefSampling implementation
    """
    def __init__(self, culture_id: str, implementation: Callable[..., Any], implementation_mask: Callable[..., Any]=None):
        self.culture_id = culture_id
        self.implementation = implementation
        self.implementation_mask = implementation_mask

    def __str__(self):
        return self.culture_id


class ApprovalCulture(Culture):
    """
    Approval cultures.
    """
    IMPARTIAL = ("impartial", psa.impartial, masks.impartial_approval_mask)
    IDENTITY = ("identity", psa.identity, masks.identity_approval_mask)
    EMPTY = ("empty", psa.empty)
    FULL = ("full", psa.full)
    RESAMPLING = ("resampling", psa.resampling)
    DISJOINT_RESAMPLING = ("disjoint_resampling", psa.disjoint_resampling)
    MOVING_RESAMPLING = ("moving_resampling", psa.moving_resampling)
    NOISE = ("noise", psa.noise)
    URN_PARTYLIST = ("urn_partylist", psa.urn_partylist)
    TRUNCATED_URN = ("truncated_urn", psa.truncated_ordinal, masks.truncated_urn_mask)
    EUCLIDEAN = ("euclidean", psa.euclidean_vcr, masks.euclidean_approval_mask)
