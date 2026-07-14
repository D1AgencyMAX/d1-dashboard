"""Core domain models shared across the pipeline."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class Sport(str, enum.Enum):
    HORSE_RACING = "horse_racing"
    GREYHOUNDS = "greyhounds"
    FOOTBALL = "football"
    TENNIS = "tennis"
    AFL = "afl"
    NRL = "nrl"
    CRICKET = "cricket"


class Side(str, enum.Enum):
    BACK = "BACK"
    LAY = "LAY"


class Decision(str, enum.Enum):
    BET = "BET"
    REJECT = "REJECT"


class RejectionReason(str, enum.Enum):
    EV_TOO_LOW = "ev_below_minimum"
    LOW_CONFIDENCE = "model_confidence_below_minimum"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    UNVERIFIED_NEWS = "unverified_material_news"
    MISSING_SELECTIONS = "missing_team_selection_or_scratches"
    MODEL_DISAGREEMENT = "model_disagreement_too_high"
    PRICE_DRIFT = "price_changed_outside_tolerance"
    SMALL_SAMPLE = "historical_sample_too_small"
    CORRELATED_EXPOSURE = "correlated_exposure_already_open"
    STARTS_TOO_SOON = "market_starts_too_soon"
    WIDE_SPREAD = "back_lay_spread_too_wide"
    STALE_DATA = "data_is_stale"
    API_UNHEALTHY = "betfair_api_or_stream_unhealthy"
    DAILY_LOSS_LIMIT = "daily_loss_limit_reached"
    WEEKLY_LOSS_LIMIT = "weekly_loss_limit_reached"
    EXPOSURE_CAP = "exposure_cap_reached"
    MARKET_CLOSED = "market_not_open"
    BELOW_MIN_ODDS = "odds_below_minimum_acceptable"
    LOWER_BOUND_FAIL = "lower_confidence_bound_below_break_even"


@dataclass
class PriceSize:
    price: float
    size: float


@dataclass
class RunnerBook:
    selection_id: int
    name: str = ""
    status: str = "ACTIVE"  # ACTIVE | REMOVED | WINNER | LOSER
    best_back: list[PriceSize] = field(default_factory=list)
    best_lay: list[PriceSize] = field(default_factory=list)
    last_price_traded: float | None = None
    total_matched: float = 0.0

    @property
    def back_price(self) -> float | None:
        return self.best_back[0].price if self.best_back else None

    @property
    def back_size(self) -> float:
        return self.best_back[0].size if self.best_back else 0.0

    @property
    def lay_price(self) -> float | None:
        return self.best_lay[0].price if self.best_lay else None


@dataclass
class MarketSnapshot:
    market_id: str
    sport: Sport
    market_type: str
    event_id: str
    event_name: str
    competition: str
    start_time: datetime
    runners: list[RunnerBook]
    status: str = "OPEN"          # OPEN | SUSPENDED | CLOSED
    in_play: bool = False
    turn_in_play_enabled: bool = False
    total_matched: float = 0.0
    total_available: float = 0.0
    # Market Base Rate (commission fraction, e.g. 0.05) from the market rules;
    # None means unknown → fall back to the configured default.
    market_base_rate: float | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def runner(self, selection_id: int) -> RunnerBook | None:
        for r in self.runners:
            if r.selection_id == selection_id:
                return r
        return None

    @property
    def active_runners(self) -> list[RunnerBook]:
        return [r for r in self.runners if r.status == "ACTIVE"]

    def seconds_to_start(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return (self.start_time - now).total_seconds()


@dataclass
class Fact:
    """A single timestamped, attributed research fact.

    Every piece of research carries its publication and collection timestamps
    so stale or unverified information can be rejected instead of silently
    affecting a bet.
    """

    source: str
    event_id: str
    fact_type: str                    # e.g. player_injury, scratching, lineup, weather
    value: Any
    published_at: datetime
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_reliability: float = 0.5   # 0..1, prior reliability of the source
    confidence: float = 0.5           # 0..1, confidence the fact was extracted correctly
    claim_key: str = ""               # canonical claim id for correlation clustering
    original_source: str = ""         # first-party origin if this is a repeat
    official: bool = False
    subject: str = ""

    def age_hours(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return (now - self.published_at).total_seconds() / 3600.0

    def is_stale(self, max_age_hours: float, now: datetime | None = None) -> bool:
        return self.age_hours(now) > max_age_hours


@dataclass
class ComponentEstimate:
    """One research component's probability estimate for a selection."""

    component: str                # matches an ensemble weight key
    probability: float
    confidence: float = 0.5      # 0..1 self-reported reliability of this estimate
    sample_size: int = 0
    correlation_group: str = ""  # components sharing a group are discounted together


@dataclass
class ProbabilityEstimate:
    market_id: str
    selection_id: int
    probability: float           # calibrated ensemble point estimate
    lower_bound: float           # conservative lower confidence bound
    upper_bound: float
    confidence: float            # aggregate model confidence 0..1
    components: list[ComponentEstimate] = field(default_factory=list)
    sample_size: int = 0
    disagreement: float = 0.0    # spread between component estimates
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Opportunity:
    market: MarketSnapshot
    selection_id: int
    selection_name: str
    side: Side
    estimate: ProbabilityEstimate
    odds: float                       # executable price when scored
    minimum_acceptable_odds: float
    expected_value: float             # commission-adjusted EV per unit stake
    commission_rate: float
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)
    data_completeness: float = 1.0
    source_quality: float = 0.5
    price_stability: float = 1.0
    calibration_quality: float = 0.5
    scored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BetRecord:
    customer_order_ref: str
    market_id: str
    selection_id: int
    selection_name: str
    sport: Sport
    event_id: str
    side: Side
    requested_price: float
    requested_size: float
    matched_price: float | None = None
    matched_size: float = 0.0
    status: str = "PENDING"           # PENDING | MATCHED | PARTIAL | LAPSED | CANCELLED | SETTLED
    placed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    settled_at: datetime | None = None
    profit: float | None = None
    mode: str = "paper"               # paper | live
    expected_value: float = 0.0
    model_probability: float = 0.0
    closing_price: float | None = None  # for closing-line-value analysis
