"""End-to-end pipeline: snapshot + research -> estimates -> opportunities.

This is the pure decision core, independent of scheduling and I/O, so the
back-tester, shadow mode and live mode all run exactly the same code path.
"""

from __future__ import annotations

import logging
from datetime import datetime

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
from .selection import scoring

log = logging.getLogger(__name__)


class DecisionPipeline:
    def __init__(
        self,
        cfg: BotConfig,
        research_modules: dict[Sport, ResearchModule],
        store: FeatureStore,
        calibrator: ShrinkageCalibrator | None = None,
        calibration_quality: float = 0.5,
    ):
        self.cfg = cfg
        self.research = research_modules
        self.store = store
        self.calibrator = calibrator or ShrinkageCalibrator()
        self.calibration_quality = calibration_quality

    # -------------------------------------------------------------- estimate

    def estimate_market(self, market: MarketSnapshot) -> dict[int, ProbabilityEstimate]:
        module = self.research.get(market.sport)
        if module is None:
            return {}
        components = module.component_estimates(market, self.store)
        market_probs = market_implied_probabilities(market)

        estimates: dict[int, ProbabilityEstimate] = {}
        for selection_id, comps in components.items():
            if not comps:
                continue
            est = ensemble.combine(
                comps,
                self.cfg.ensemble_weights,
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
        commission = self.cfg.betfair.commission_rate
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
                price_stability=1.0,
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
