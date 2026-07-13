"""News intelligence: LLM-assisted fact extraction and classification.

The LLM is used ONLY to extract and classify facts from articles — who is
affected, how certain the status is, whether the source is official — never
to invent probabilities. Extracted facts flow into the feature store where
staleness and correlation rules apply, and an already-priced estimate is made
by comparing publication time against Betfair price movement.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from ..models import Fact

log = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a sports news fact extractor for a betting research system.
Extract only facts that are explicitly stated in the article. Do not infer,
speculate, or estimate probabilities.

Return a JSON array. Each element:
{
  "subject": "who or what is affected (player/runner/team/venue)",
  "fact_type": "player_injury | scratching | lineup_change | weather | suspension | travel | other",
  "status": "confirmed_out | confirmed_in | doubtful | rumoured",
  "event_hint": "event, fixture or race the fact relates to, verbatim from the article",
  "source_class": "official_team_announcement | accredited_journalist | wire_service | aggregator | social_media",
  "quote": "the exact sentence supporting the fact"
}

Return [] if the article contains no concrete, attributable facts.
Article published at: {published_at}
Article:
{article}
"""

SOURCE_RELIABILITY = {
    "official_team_announcement": 0.98,
    "accredited_journalist": 0.85,
    "wire_service": 0.80,
    "aggregator": 0.55,
    "social_media": 0.35,
}

STATUS_CONFIDENCE = {
    "confirmed_out": 0.95,
    "confirmed_in": 0.95,
    "doubtful": 0.6,
    "rumoured": 0.3,
}


@dataclass
class Article:
    source: str
    url: str
    text: str
    published_at: datetime
    event_id: str = ""


class NewsExtractor:
    """Extracts structured facts from articles via the Anthropic API.

    Requires ANTHROPIC_API_KEY and the optional `anthropic` dependency; when
    unavailable, extraction is skipped (never guessed).
    """

    def __init__(self, model: str = "claude-sonnet-5"):
        self.model = model
        self._client = None
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                import anthropic

                self._client = anthropic.Anthropic()
            except ImportError:
                log.warning("anthropic package not installed; news extraction disabled")

    @property
    def available(self) -> bool:
        return self._client is not None

    def extract(self, article: Article) -> list[Fact]:
        if not self._client:
            return []
        prompt = EXTRACTION_PROMPT.replace("{article}", article.text[:12000]).replace(
            "{published_at}", article.published_at.isoformat()
        )
        response = self._client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        try:
            start, end = raw.index("["), raw.rindex("]") + 1
            items = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            log.warning("news extraction returned unparseable output for %s", article.url)
            return []

        facts: list[Fact] = []
        now = datetime.now(timezone.utc)
        for item in items:
            source_class = item.get("source_class", "aggregator")
            status = item.get("status", "rumoured")
            facts.append(
                Fact(
                    source=article.source,
                    event_id=article.event_id,
                    fact_type=item.get("fact_type", "other"),
                    value=status,
                    published_at=article.published_at,
                    collected_at=now,
                    source_reliability=SOURCE_RELIABILITY.get(source_class, 0.5),
                    confidence=STATUS_CONFIDENCE.get(status, 0.5),
                    subject=item.get("subject", ""),
                    official=source_class == "official_team_announcement",
                    original_source=article.source,
                )
            )
        return facts


def already_priced_probability(
    fact: Fact,
    price_moves: list[tuple[datetime, float]],
    material_move_pct: float = 0.03,
) -> float:
    """Estimate the probability the market already reflects a fact.

    Compares the fact's publication timestamp against subsequent Betfair price
    movement: a material move after publication suggests incorporation. This
    stops the model repeatedly reacting to the same report.

    price_moves: [(timestamp, implied_probability)] samples for the affected
    selection, ordered by time.
    """
    before = [p for t, p in price_moves if t <= fact.published_at]
    after = [p for t, p in price_moves if t > fact.published_at]
    if not before or not after:
        return 0.5  # unknown → neutral
    baseline, latest = before[-1], after[-1]
    if baseline <= 0:
        return 0.5
    move = abs(latest - baseline) / baseline
    hours_elapsed = (
        max(t for t, _ in price_moves) - fact.published_at
    ).total_seconds() / 3600.0
    # A big move soon after publication → likely priced; an old fact with no
    # move is probably immaterial (also effectively priced).
    if move >= material_move_pct:
        return min(0.95, 0.6 + move * 4.0)
    if hours_elapsed > 6:
        return 0.75
    return 0.3 + 0.05 * hours_elapsed
