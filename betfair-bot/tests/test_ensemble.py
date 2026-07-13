import pytest

from betfair_bot.modeling.ensemble import combine, effective_weights, normalise_market
from betfair_bot.models import ComponentEstimate

WEIGHTS = {
    "historical_model": 0.25,
    "recent_form": 0.20,
    "availability": 0.15,
    "independent_market_consensus": 0.15,
    "news_sentiment": 0.03,
}


def ce(component, p, conf=0.8, n=500, group=""):
    return ComponentEstimate(
        component=component, probability=p, confidence=conf,
        sample_size=n, correlation_group=group,
    )


def test_weighted_average():
    comps = [ce("historical_model", 0.40), ce("independent_market_consensus", 0.30)]
    est = combine(comps, WEIGHTS)
    # Equal base weights (0.25*0.8 vs 0.15*0.8) → weighted toward 0.40.
    assert 0.30 < est.probability < 0.40
    assert est.lower_bound < est.probability < est.upper_bound


def test_correlated_sources_do_not_stack():
    # Five news components repeating the same claim must not dominate.
    independent = [ce("historical_model", 0.40), ce("news_sentiment", 0.80)]
    est_single = combine(independent, WEIGHTS)

    repeated = [ce("historical_model", 0.40)] + [
        ce("news_sentiment", 0.80, group="injury-claim-1") for _ in range(5)
    ]
    est_repeated = combine(repeated, WEIGHTS)
    # The clustered five count as one: same result within tolerance.
    assert est_repeated.probability == pytest.approx(est_single.probability, abs=0.01)


def test_correlation_group_splits_weight():
    comps = [
        ce("historical_model", 0.4),
        ce("news_sentiment", 0.8, group="g"),
        ce("news_sentiment", 0.8, group="g"),
    ]
    w = effective_weights(comps, WEIGHTS)
    assert w[1] == pytest.approx(w[2])
    # Combined news weight equals a single occurrence's weight share.
    solo = effective_weights([ce("historical_model", 0.4), ce("news_sentiment", 0.8)], WEIGHTS)
    assert w[1] + w[2] == pytest.approx(solo[1], rel=1e-6)


def test_disagreement_widens_bounds():
    agree = combine([ce("historical_model", 0.40), ce("recent_form", 0.41)], WEIGHTS)
    disagree = combine([ce("historical_model", 0.30), ce("recent_form", 0.55)], WEIGHTS)
    assert disagree.disagreement > agree.disagreement
    assert (disagree.upper_bound - disagree.lower_bound) > (agree.upper_bound - agree.lower_bound)
    assert disagree.confidence < agree.confidence


def test_normalise_market_sums_to_one():
    ests = {
        1: combine([ce("historical_model", 0.5)], WEIGHTS, selection_id=1),
        2: combine([ce("historical_model", 0.4)], WEIGHTS, selection_id=2),
        3: combine([ce("historical_model", 0.3)], WEIGHTS, selection_id=3),
    }
    normalise_market(ests)
    assert sum(e.probability for e in ests.values()) == pytest.approx(1.0, abs=1e-6)


def test_empty_components_raise():
    with pytest.raises(ValueError):
        combine([], WEIGHTS)
