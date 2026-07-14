"""End-to-end pipeline: snapshot + research -> estimates -> opportunities.

This is the pure decision core, independent of scheduling and I/O, so the
back-tester, shadow mode and live mode all run exactly the same code path.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from .betfair.ticks import spread_ticks
from .config import BotConfig
from .modeling import ensemble
from .modeling.calibration import ShrinkageCalibrator
from .modeling.market_prior import market_implied_probabilities
from .models import (
    MarketSnapshot,
    Opportunity,
    ProbabilityEstimate,
    RejectionReason,
    Sport,
)
from .research.base import ResearchModule
from .research.feature_store import FeatureStore
from .research.orderbook import order_book_component
from .selection import costs, scoring

log = logging.getLogger(__name__)

# Any object with .calibrate(model_p, market_p) -> float works here
# (ShrinkageCalibrator until fitted, LogisticCalibrator once graded data exists).
PriceHistoryFn = Callable[[str, int], list[tuple[datetime, float]]]


class DecisionPipeline:
    def __init__(
        self,
        cfg: BotConfig,
        research_modules: dict[Sport, ResearchModule],
        store: FeatureStore,
        calibrator: ShrinkageCalibrator | None = None,
        calibration_quality: float = 0.5,
        price_history_fn: PriceHistoryFn | None = None,
        sport_weights: dict[Sport, dict[str, float]] | None = None,
    ):
        self.cfg = cfg
        self.research = research_modules
        self.store = store
        self.calibrator = calibrator or ShrinkageCalibrator()
        self.calibration_quality = calibration_quality
        self.price_history_fn = price_history_fn
        # Per-sport learned weights override the config priors once fitted.
        self.sport_weights = sport_weights or {}

    def weights_for(self, sport: Sport) -> dict[str, float]:
        return self.sport_weights.get(sport, self.cfg.ensemble_weights)

    # -------------------------------------------------------------- estimate

    def estimate_market(self, market: MarketSnapshot) -> dict[int, ProbabilityEstimate]:
        module = self.research.get(market.sport)
        if module is None:
            return {}
        components = module.component_estimates(market, self.store)
        market_probs = market_implied_probabilities(market)
        weights = self.weights_for(market.sport)

        estimates: dict[int, ProbabilityEstimate] = {}
        for selection_id, comps in components.items():
            if not comps:
                continue
            # Order-book behaviour (pressure, steam, late volume) joins the
            # ensemble as its own component when a book is visible.
            runner = market.runner(selection_id)
            if runner is not None:
                history = (
                    self.price_history_fn(market.market_id, selection_id)
                    if self.price_history_fn
                    else []
                )
                ob = order_book_component(market, runner, history)
                if ob is not None:
                    comps = comps + [ob]
            est = ensemble.combine(
                comps,
                weights,
                market_id=market.market_id,
                selection_id=selection_id,
            )
            # Shrink toward the market until live evidence justifies more trust.
            market_p = market_probs.get(selection_id)
            shift = self.calibrator.calibrate(est.probability, market_p) - est.probability
            est.probability += shift
            est.lower_bound = max(0.0, est.lower_bound + shift)
            est.upper_bound = min(1.0, est.upper_bound + shift)
            estimates[selection_id] = est

        # Win markets must sum to 1 across the field.
        if market.market_type in ("WIN", "MATCH_ODDS") and len(estimates) == len(market.active_runners):
            ensemble.normalise_market(estimates)
        return estimates

    # ------------------------------------------------------------- opportunities

    def evaluate_market(
        self,
        market: MarketSnapshot,
        api_healthy: bool = True,
        now: datetime | None = None,
    ) -> tuple[list[Opportunity], dict[int, list[RejectionReason]]]:
        """Score every selection; return qualified opportunities + rejections."""
        module = self.research.get(market.sport)
        if module is None:
            return [], {}
        sel_cfg = self.cfg.selection
        # Per-market commission: the market's own base rate (AU racing often
        # carries 6-10%) plus any configured premium-charge haircut.
        commission = costs.market_commission(
            market,
            fallback_rate=self.cfg.betfair.commission_rate,
            premium_charge_rate=self.cfg.betfair.premium_charge_rate,
        )
        research_cfg = self.cfg.research

        unverified_news = self.store.has_unverified_material_news(
            market.event_id,
            reliability_floor=float(research_cfg.get("news_reliability_floor", 0.6)),
            now=now,
        )
        selections_ok = module.selections_confirmed(market, self.store, now=now)
        completeness = self.store.data_completeness(
            market.event_id, module.required_fact_types, now=now
        )
        data_fresh = (
            (now or market.captured_at) is not None
        )  # book freshness re-checked at execution; here we gate on fact staleness via store

        qualified: list[Opportunity] = []
        rejections: dict[int, list[RejectionReason]] = {}

        for selection_id, estimate in self.estimate_market(market).items():
            runner = market.runner(selection_id)
            if runner is None or not runner.back_price:
                continue
            reasons = scoring.check_rejections(
                market,
                estimate,
                odds=runner.back_price,
                available_size=runner.back_size,
                cfg=sel_cfg,
                commission=commission,
                has_unverified_material_news=unverified_news,
                selections_confirmed=selections_ok,
                api_healthy=api_healthy,
                data_fresh=data_fresh,
                spread_ticks=spread_ticks(runner.back_price, runner.lay_price),
                now=now,
            )
            if reasons:
                rejections[selection_id] = reasons
                continue
            opp = scoring.build_opportunity(
                market,
                estimate,
                sel_cfg,
                commission,
                source_quality=self._source_quality(market),
                price_stability=None,  # derived from the back/lay spread
                calibration_quality=self.calibration_quality,
                data_completeness=completeness,
            )
            if opp is not None:
                qualified.append(opp)

        return scoring.rank_opportunities(qualified), rejections

    def _source_quality(self, market: MarketSnapshot) -> float:
        facts = self.store.facts(market.event_id)
        if not facts:
            return 0.5
        return sum(f.source_reliability for f in facts) / len(facts)
