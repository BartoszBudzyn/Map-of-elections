from collections.abc import Callable
from enum import Enum
from typing import Any

import prefsampling.approval as psa
import prefsampling.ordinal as pso

import mapof.elections.cultures.compass as comp
import mapof.elections.cultures.prefsampling_mask as masks
import mapof.elections.cultures.pseudo_cultures as pseudo

class Culture(Enum):
    """
    An enum of election statistical cultures (i.e. ways of sampling elections).
    :param culture_id: an ID as defined in the original mapof-elections
    :param implementation: PrefSampling sampling function (or mapof-elections function, if there is no PrefSampling implementation)
    :param implementation_mask: mapof-elections mask for the PrefSampling implementation
    """
    def __init__(self, culture_id: str, implementation: Callable[..., Any], implementation_mask: Callable[..., Any]|None=None):
        if not callable(implementation):
            raise ValueError(f"implementation must be callable, got {type(implementation)}")
        if implementation_mask is not None and not callable(implementation_mask):
            raise ValueError(f"implementation_mask must be callable or None, got {type(implementation_mask)}")

        self.culture_id = culture_id
        self.implementation = implementation
        self.implementation_mask = implementation_mask

    def __str__(self):
        return self.culture_id


class ApprovalCulture(Culture):
    """An enum of statistical cultures for approval elections."""
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

class OrdinalCulture(Culture):
    """An enum of statistical cultures for ordinal elections."""
    IDENTITY = ("identity", pso.identity)
    IMPARTIAL = ("impartial", pso.impartial)
    IAC = ("iac", pso.impartial_anonymous)
    STRATIFICATION = ("stratification", pso.impartial_anonymous)
    ANTAGONISM = ("antagonism", comp.generate_antagonism_votes)
    URN = ("urn", pso.urn)
    DIDI = ("didi", pso.didi)
    PLACKETT_LUCE = ("plackett-luce", pso.plackett_luce)
    WALSH = ("walsh", pso.single_peaked_walsh)
    SPOC = ("spoc", pso.single_peaked_circle)
    SC = ("single-crossing", pso.single_crossing)
    APPROX_UNIFORMITY = ("approx_uniformity", comp.generate_approx_uniformity_votes)
    APPROX_STRATIFICATION = ("approx_stratification", comp.generate_approx_stratification_votes)
    EUCLIDEAN = ("euclidean", pso.euclidean, masks.euclidean_approval_mask)
    GROUP_SEPARABLE = ("group-separable", pso.group_separable, masks.group_separable_mask)
    MALLOWS = ("mallows", pso.mallows)
    NORM_MALLOWS = ("norm-mallows", pso.norm_mallows, masks.norm_mallows_mask)

class PseudoOrdinalCulture(Culture):
    """An enum of statistical cultures for pseudo-ordinal elections."""
    PSEUDO_IDENTITY = ("pseudo_identity", pseudo.pseudo_identity)
    PSEUDO_UNIFORMITY = ("pseudo_uniformity", pseudo.pseudo_uniformity)
    PSEUDO_ANTAGONISM = ("pseudo_antagonism", pseudo.pseudo_antagonism)
    PSEUDO_STRATIFICATION = ("pseudo_stratification", pseudo.pseudo_stratification)
    PSEUDO_UNID = ("pseudo_unid", pseudo.pseudo_unid)
    PSEUDO_ANID = ("pseudo_anid", pseudo.pseudo_anid)
    PSEUDO_STID = ("pseudo_stid", pseudo.pseudo_stid)
    PSEUDO_ANUN = ("pseudo_anun", pseudo.pseudo_anun)
    PSEUDO_STUN = ("pseudo_stun", pseudo.pseudo_stun)
    PSEUDO_STAN = ("pseudo_stan", pseudo.pseudo_stan)
