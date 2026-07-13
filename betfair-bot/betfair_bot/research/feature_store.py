"""Timestamped feature store with staleness rejection.

Every fact carries published_at / collected_at / reliability / confidence so
old injury articles or unconfirmed posts cannot silently affect a bet.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from ..models import Fact
from .correlation import cluster_claims


class FeatureStore:
    def __init__(self, max_fact_age_hours: float = 48.0):
        self.max_fact_age_hours = max_fact_age_hours
        self._facts: dict[str, list[Fact]] = defaultdict(list)

    def add(self, fact: Fact) -> None:
        self._facts[fact.event_id].append(fact)

    def add_many(self, facts: list[Fact]) -> None:
        for f in facts:
            self.add(f)

    def facts(
        self,
        event_id: str,
        fact_type: str | None = None,
        now: datetime | None = None,
        include_stale: bool = False,
    ) -> list[Fact]:
        """Fresh facts for an event, deduplicated by underlying claim.

        Duplicate reports of the same claim collapse to a single, best-sourced
        fact so repeated coverage never counts as independent confirmation.
        """
        rows = self._facts.get(event_id, [])
        if fact_type:
            rows = [f for f in rows if f.fact_type == fact_type]
        if not include_stale:
            rows = [f for f in rows if not f.is_stale(self.max_fact_age_hours, now)]
        return cluster_claims(rows)

    def has_unverified_material_news(
        self,
        event_id: str,
        reliability_floor: float,
        material_types: tuple[str, ...] = ("player_injury", "scratching", "lineup_change"),
        now: datetime | None = None,
    ) -> bool:
        """True when a material claim exists only below the reliability floor.

        A rumoured injury with no official confirmation blocks betting on the
        affected event rather than being guessed around.
        """
        for fact in self.facts(event_id, now=now):
            if fact.fact_type not in material_types:
                continue
            if fact.official or fact.source_reliability >= reliability_floor:
                continue
            return True
        return False

    def data_completeness(self, event_id: str, required_types: list[str], now: datetime | None = None) -> float:
        """Fraction of required fact types present and fresh for the event."""
        if not required_types:
            return 1.0
        present = {f.fact_type for f in self.facts(event_id, now=now)}
        return sum(1 for t in required_types if t in present) / len(required_types)
