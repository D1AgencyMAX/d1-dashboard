"""Tests for the edge-finding engine: model fitting, weight learning,
logistic calibration and order-book signals.

The fitting tests use synthetic data generated from known parameters, so
"does the fitter recover the truth?" has an objective answer.
"""

import math
import random
from datetime import datetime, timedelta, timezone

import pytest

from betfair_bot.modeling.dixon_coles import MatchResult, fit_ratings, holdout_log_loss
from betfair_bot.modeling.elo_fit import TennisMatch, fit_elo
from betfair_bot.modeling.logistic_calibration import LogisticCalibrator
from betfair_bot.modeling.weight_optimizer import (
    GradedSample,
    fit_weights,
    prune_useless_components,
)
from betfair_bot.models import MarketSnapshot, PriceSize, RunnerBook, Sport
from betfair_bot.research.orderbook import (
    book_pressure,
    order_book_component,
    price_momentum,
)

NOW = datetime(2026, 7, 13, 2, 0, tzinfo=timezone.utc)
rng = random.Random(42)


def _poisson(lam: float) -> int:
    # Knuth sampler — fine for test-scale lambda.
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


class TestDixonColesFitter:
    def _synthetic(self, n_rounds=60):
        true = {
            "Strong": (1.4, 0.75),
            "Good": (1.15, 0.9),
            "Mid": (1.0, 1.0),
            "Weak": (0.8, 1.2),
        }
        teams = list(true)
        matches = []
        day = 0
        for _ in range(n_rounds):
            for h in teams:
                for a in teams:
                    if h == a:
                        continue
                    ha, hd = true[h]
                    aa, ad = true[a]
                    lam_h = 1.35 * ha * ad * 1.25
                    lam_a = 1.35 * aa * hd
                    matches.append(MatchResult(
                        h, a, _poisson(lam_h), _poisson(lam_a),
                        NOW - timedelta(days=720 - day),
                    ))
                    day += 1
        return true, matches

    def test_recovers_team_ordering(self):
        true, matches = self._synthetic()
        ratings, home_adv = fit_ratings(matches, as_of=NOW)
        # Net strength ordering must match the generator.
        strength = {t: r.attack / r.defence for t, r in ratings.items()}
        assert strength["Strong"] > strength["Good"] > strength["Mid"] > strength["Weak"]
        # Home advantage recovered near 1.25.
        assert 1.1 < home_adv < 1.45
        # Attack params recovered within tolerance.
        assert ratings["Strong"].attack == pytest.approx(1.4, abs=0.2)
        assert ratings["Weak"].attack == pytest.approx(0.8, abs=0.15)

    def test_beats_uniform_on_holdout(self):
        _, matches = self._synthetic()
        matches.sort(key=lambda m: m.played_at)
        split = int(len(matches) * 0.8)
        ratings, home_adv = fit_ratings(matches[:split], as_of=NOW)
        ll = holdout_log_loss(ratings, home_adv, matches[split:])
        assert ll < math.log(3)  # better than uniform H/D/A

    def test_time_decay_prefers_recent_form(self):
        # Team was bad long ago, good recently — rating should reflect recent.
        old = [
            MatchResult("X", "Y", 0, 3, NOW - timedelta(days=700 + i))
            for i in range(20)
        ]
        recent = [
            MatchResult("X", "Y", 3, 0, NOW - timedelta(days=10 + i))
            for i in range(20)
        ]
        ratings, _ = fit_ratings(old + recent, as_of=NOW, half_life_days=90)
        assert ratings["X"].attack > ratings["Y"].attack

    def test_empty_input(self):
        ratings, home_adv = fit_ratings([])
        assert ratings == {}


class TestWeightOptimizer:
    def _samples(self, n=600):
        """Component A is informative; component B is pure noise."""
        samples = []
        for _ in range(n):
            p_true = rng.uniform(0.1, 0.9)
            outcome = 1 if rng.random() < p_true else 0
            samples.append(GradedSample(
                component_probs={
                    "informative": min(0.95, max(0.05, p_true + rng.gauss(0, 0.03))),
                    "noise": rng.uniform(0.1, 0.9),
                },
                outcome=outcome,
            ))
        return samples

    def test_informative_component_wins_weight(self):
        fit = fit_weights(self._samples(), ["informative", "noise"])
        assert fit.weights["informative"] > 0.85
        assert fit.log_loss < fit.baseline_log_loss  # beats equal weights

    def test_marginal_value_identifies_noise(self):
        fit = fit_weights(self._samples(), ["informative", "noise"])
        assert fit.marginal_value["informative"] > 0.05   # removing it hurts a lot
        useless = prune_useless_components(fit, min_marginal=0.01)
        assert "noise" in useless
        assert "informative" not in useless

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            fit_weights([], ["a"])


class TestLogisticCalibrator:
    def _overconfident(self, n=2000):
        """Model is systematically overconfident: true p = shrink(model p)."""
        model_p, market_p, outcomes = [], [], []
        for _ in range(n):
            mp = rng.uniform(0.05, 0.95)
            true_p = 0.5 + 0.6 * (mp - 0.5)      # true probability closer to 0.5
            model_p.append(mp)
            market_p.append(min(0.95, max(0.05, true_p + rng.gauss(0, 0.02))))
            outcomes.append(1 if rng.random() < true_p else 0)
        return model_p, market_p, outcomes

    def test_fit_reduces_log_loss(self):
        mp, kp, y = self._overconfident()
        raw = LogisticCalibrator()  # identity on model prob
        fitted = LogisticCalibrator.fit(mp, kp, y)
        assert fitted.log_loss(mp, kp, y) < raw.log_loss(mp, kp, y) - 0.01

    def test_learns_shrinkage_and_market_trust(self):
        mp, kp, y = self._overconfident()
        fitted = LogisticCalibrator.fit(mp, kp, y)
        # Market carries most of the signal here; model logit gets shrunk.
        assert fitted.b > fitted.a
        # Overconfident model → combined weight on model logit below 1.
        assert fitted.a < 1.0

    def test_works_without_market_price(self):
        cal = LogisticCalibrator(a=0.5, b=0.4, c=0.0)
        p = cal.calibrate(0.8, None)
        assert 0.5 < p < 0.8  # shrunk toward 0.5, market term dropped


class TestOrderBookSignals:
    def _runner(self, back_sizes, lay_sizes, sid=1, price=3.0):
        return RunnerBook(
            selection_id=sid, name="R",
            best_back=[PriceSize(price - i * 0.05, s) for i, s in enumerate(back_sizes)],
            best_lay=[PriceSize(price + 0.05 + i * 0.05, s) for i, s in enumerate(lay_sizes)],
        )

    def _market(self, runners):
        return MarketSnapshot(
            market_id="1.1", sport=Sport.HORSE_RACING, market_type="WIN",
            event_id="e1", event_name="Race", competition="X",
            start_time=NOW + timedelta(hours=1), runners=runners,
            total_matched=50_000, captured_at=NOW,
        )

    def test_book_pressure_direction(self):
        heavy_lay = self._runner(back_sizes=[100, 80], lay_sizes=[3000, 2000])
        heavy_back = self._runner(back_sizes=[3000, 2000], lay_sizes=[100, 80])
        assert book_pressure(heavy_lay) < -0.5    # support: money offering our back side
        assert book_pressure(heavy_back) > 0.5

    def test_momentum(self):
        firming = [(NOW - timedelta(minutes=60 - i), 0.30 + i * 0.002) for i in range(30)]
        drifting = [(NOW - timedelta(minutes=60 - i), 0.30 - i * 0.002) for i in range(30)]
        assert price_momentum(firming) > 0
        assert price_momentum(drifting) < 0
        assert price_momentum([]) == 0.0

    def test_component_tilts_market_prob_bounded(self):
        r1 = self._runner([100, 80], [3000, 2000], sid=1, price=3.0)
        r2 = self._runner([500, 400], [500, 400], sid=2, price=1.6)
        market = self._market([r1, r2])
        comp = order_book_component(market, r1, history=[])
        assert comp is not None
        assert comp.component == "betfair_order_book"
        # Lay-side depth → tilt below the market-implied probability, but
        # never beyond the ±6% relative cap.
        from betfair_bot.modeling.market_prior import market_implied_probabilities
        base = market_implied_probabilities(market)[1]
        assert comp.probability < base
        assert abs(comp.probability - base) / base <= 0.061

    def test_thin_book_low_confidence(self):
        thin = self._runner([10], [10])
        deep = self._runner([10_000, 8_000, 6_000], [10_000, 8_000, 6_000])
        market = self._market([thin, deep])
        c_thin = order_book_component(market, thin, [])
        c_deep = order_book_component(market, deep, [])
        assert c_thin.confidence < c_deep.confidence


class TestEloFitter:
    def test_dominant_player_rises(self):
        matches = [
            TennisMatch("Ace", "Journeyman", "hard", NOW - timedelta(days=100 - i))
            for i in range(30)
        ]
        ratings = fit_elo(matches)
        assert ratings["Ace"].elo["hard"] > 1600
        assert ratings["Journeyman"].elo["hard"] < 1400
        # Cross-surface transfer: clay moved, but less than hard.
        hard_gain = ratings["Ace"].elo["hard"] - 1500
        clay_gain = ratings["Ace"].elo["clay"] - 1500
        assert 0 < clay_gain < hard_gain

    def test_upset_moves_more_than_expected_win(self):
        base = fit_elo([
            TennisMatch("Ace", "Journeyman", "hard", NOW - timedelta(days=50 - i))
            for i in range(20)
        ])
        ace_before = base["Ace"].elo["hard"]
        after = fit_elo([TennisMatch("Journeyman", "Ace", "hard", NOW)], initial=base)
        upset_drop = ace_before - after["Ace"].elo["hard"]
        assert upset_drop > 10  # losing as a heavy favourite costs plenty
