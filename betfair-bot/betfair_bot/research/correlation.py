"""Source-correlation: collapse duplicate reports into single claims.

Five articles repeating one injury report are one piece of evidence, not
five. Facts are clustered by their canonical claim key; each cluster keeps
its best representative, preferring official / first-party confirmation.
"""

from __future__ import annotations

from collections import defaultdict

from ..models import Fact


def claim_key(fact: Fact) -> str:
    """Canonical identity of the underlying claim."""
    if fact.claim_key:
        return fact.claim_key
    return f"{fact.event_id}|{fact.fact_type}|{fact.subject}|{fact.value}".lower()


def cluster_claims(facts: list[Fact]) -> list[Fact]:
    """Reduce a list of facts to one representative per underlying claim.

    Selection order within a cluster: official sources first, then higher
    source reliability, then earliest publication (closest to the original
    source). The representative's confidence is nudged up slightly when
    multiple *distinct original sources* repeat the claim — never when the
    same origin is syndicated.
    """
    clusters: dict[str, list[Fact]] = defaultdict(list)
    for fact in facts:
        clusters[claim_key(fact)].append(fact)

    representatives: list[Fact] = []
    for members in clusters.values():
        best = sorted(
            members,
            key=lambda f: (not f.official, -f.source_reliability, f.published_at),
        )[0]
        origins = {f.original_source or f.source for f in members}
        if len(origins) > 1 and not best.official:
            independent = min(len(origins) - 1, 3)
            best.confidence = min(1.0, best.confidence + 0.05 * independent)
        representatives.append(best)
    return representatives
