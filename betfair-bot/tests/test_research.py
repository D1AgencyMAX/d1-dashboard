from datetime import datetime, timedelta, timezone

import pytest

from betfair_bot.models import Fact, MarketSnapshot, PriceSize, RunnerBook, Sport
from betfair_bot.research.correlation import cluster_claims
from betfair_bot.research.feature_store import FeatureStore
from betfair_bot.research.football import (
    FootballResearch,
    TeamRating,
    match_odds_probs,
    over_under_25,
    score_grid,
)
from betfair_bot.research.news import already_priced_probability
from betfair_bot.research.racing import RunnerForm, softmax_probabilities
from betfair_bot.research.tennis import elo_win_probability
from betfair_bot.research.afl_nrl import margin_to_win_probability

NOW = datetime(2026, 7, 13, 2, 0, tzinfo=timezone.utc)


def fact(source, published_hours_ago=1.0, reliability=0.9, official=False,
         subject="Player X", value="out", original=""):
    return Fact(
        source=source, event_id="e1", fact_type="player_injury", value=value,
        published_at=NOW - timedelta(hours=published_hours_ago),
        collected_at=NOW, source_reliability=reliability,
        confidence=0.9, official=official, subject=subject,
        original_source=original or source,
    )


class TestFeatureStore:
    def test_stale_facts_rejected(self):
        store = FeatureStore(max_fact_age_hours=48)
        store.add(fact("fresh", published_hours_ago=2))
        store.add(fact("old", published_hours_ago=72, subject="Player Y"))
        facts = store.facts("e1", now=NOW)
        assert [f.source for f in facts] == ["fresh"]

    def test_duplicate_claims_collapse(self):
        store = FeatureStore()
        # Five articles repeating one injury (same subject/value → same claim).
        for i in range(5):
            store.add(fact(f"outlet{i}", original="original-wire"))
        facts = store.facts("e1", now=NOW)
        assert len(facts) == 1

    def test_official_source_preferred(self):
        rows = [
            fact("blog", reliability=0.4),
            fact("club", reliability=0.98, official=True),
            fact("paper", reliability=0.85),
        ]
        best = cluster_claims(rows)
        assert len(best) == 1
        assert best[0].source == "club"

    def test_unverified_material_news_flag(self):
        store = FeatureStore()
        store.add(fact("rumour-account", reliability=0.3))
        assert store.has_unverified_material_news("e1", reliability_floor=0.6, now=NOW)
        store.add(fact("club", reliability=0.98, official=True))
        # Official confirmation of the same claim clears the flag.
        assert not store.has_unverified_material_news("e1", reliability_floor=0.6, now=NOW)


class TestFootballModel:
    def test_score_grid_sums_to_one(self):
        grid = score_grid(1.5, 1.1)
        assert sum(sum(row) for row in grid) == pytest.approx(1.0)

    def test_match_odds_sane(self):
        home, draw, away = match_odds_probs(score_grid(1.8, 0.9))
        assert home > away          # stronger attack wins more
        assert home + draw + away == pytest.approx(1.0)
        assert 0.1 < draw < 0.4

    def test_over_under(self):
        over_hi, under_hi = over_under_25(score_grid(2.2, 1.8))
        over_lo, under_lo = over_under_25(score_grid(0.8, 0.7))
        assert over_hi > 0.5 > over_lo
        assert over_hi + under_hi == pytest.approx(1.0)

    def test_component_estimates_include_market_and_model(self):
        runners = [
            RunnerBook(1, "Arsenal", best_back=[PriceSize(2.0, 500)], best_lay=[PriceSize(2.02, 500)]),
            RunnerBook(2, "Chelsea", best_back=[PriceSize(4.0, 500)], best_lay=[PriceSize(4.1, 500)]),
            RunnerBook(3, "The Draw", best_back=[PriceSize(3.8, 500)], best_lay=[PriceSize(3.9, 500)]),
        ]
        market = MarketSnapshot(
            market_id="1.1", sport=Sport.FOOTBALL, market_type="MATCH_ODDS",
            event_id="e1", event_name="Arsenal v Chelsea", competition="EPL",
            start_time=NOW + timedelta(hours=6), runners=runners, total_matched=200_000,
        )
        module = FootballResearch(ratings={
            "Arsenal": TeamRating(attack=1.3, defence=0.85, sample_size=400),
            "Chelsea": TeamRating(attack=1.1, defence=0.95, sample_size=400),
        })
        comps = module.component_estimates(market, FeatureStore())
        for sid in (1, 2, 3):
            names = {c.component for c in comps[sid]}
            assert "independent_market_consensus" in names
            assert "historical_model" in names
        model_home = next(c for c in comps[1] if c.component == "historical_model")
        model_away = next(c for c in comps[2] if c.component == "historical_model")
        assert model_home.probability > model_away.probability


class TestOtherModels:
    def test_elo(self):
        assert elo_win_probability(1600, 1500) > 0.5
        assert elo_win_probability(1500, 1500) == pytest.approx(0.5)

    def test_margin_model(self):
        assert margin_to_win_probability(0.0, 36.0) == pytest.approx(0.5)
        assert margin_to_win_probability(20.0, 36.0) > 0.7

    def test_racing_softmax(self):
        probs = softmax_probabilities({1: 0.8, 2: 0.6, 3: 0.4})
        assert sum(probs.values()) == pytest.approx(1.0)
        assert probs[1] > probs[2] > probs[3]

    def test_runner_form_score_bounds(self):
        best = RunnerForm(speed_rating=1, distance_record=1, track_going_record=1,
                          barrier_score=1, weight_score=1, jockey_trainer_score=1,
                          freshness_score=1, class_change_score=1, pace_score=1)
        assert best.feature_score() == pytest.approx(1.0)


class TestAlreadyPriced:
    def test_material_move_after_publication_means_priced(self):
        f = fact("wire", published_hours_ago=3)
        moves = [
            (NOW - timedelta(hours=4), 0.40),
            (NOW - timedelta(hours=2), 0.34),  # 15% drop after the news
            (NOW - timedelta(hours=1), 0.335),
        ]
        assert already_priced_probability(f, moves) > 0.7

    def test_no_move_recent_fact_probably_not_priced(self):
        f = fact("wire", published_hours_ago=0.5)
        moves = [
            (NOW - timedelta(hours=2), 0.40),
            (NOW - timedelta(minutes=10), 0.401),
        ]
        assert already_priced_probability(f, moves) < 0.5
