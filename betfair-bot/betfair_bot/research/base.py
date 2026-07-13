"""Research module interface.

Each sport implements a ResearchModule that turns a market snapshot plus the
feature store into per-selection component estimates. The ensemble engine —
not the sport module — decides how the components combine.
"""

from __future__ import annotations

import abc
from datetime import datetime

from ..models import ComponentEstimate, MarketSnapshot
from .feature_store import FeatureStore


class ResearchModule(abc.ABC):
    """Produces component probability estimates for every active selection."""

    #: fact types this sport needs before data_completeness reaches 1.0
    required_fact_types: list[str] = []

    @abc.abstractmethod
    def component_estimates(
        self,
        market: MarketSnapshot,
        store: FeatureStore,
    ) -> dict[int, list[ComponentEstimate]]:
        """selection_id -> component estimates (keys must match ensemble weights)."""

    def selections_confirmed(
        self, market: MarketSnapshot, store: FeatureStore, now: datetime | None = None
    ) -> bool:
        """Whether final fields/line-ups/scratchings are known for this market.

        Default: confirmed. Sports where late changes are material override
        this so a bet is never placed on an unconfirmed field.
        """
        return True
