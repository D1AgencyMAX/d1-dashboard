"""Historical back-test harness (Stage 1 of edge validation).

Replays point-in-time market snapshots through the same DecisionPipeline used
live, applies realistic commission/liquidity/slippage, and reports the metrics
that decide whether the system ever goes near real money: log loss, Brier,
calibration, return on turnover, drawdown, risk-adjusted return, breakdowns by
odds band and sport, and closing-line value.

The harness consumes an iterable of (snapshot, outcomes) pairs so any
point-in-time data source (Betfair historical data files, recorded snapshots
from shadow mode) can drive it. Walk-forward retraining plugs in via the
`retrain` callback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Iterable

from ..modeling.calibration import brier_score, calibration_bins, log_loss
from ..models import MarketSnapshot
from ..pipeline import DecisionPipeline
from ..risk.engine import RiskEngine


@dataclass
class BacktestBet:
    market_id: str
    selection_id: int
    sport: str
    odds: float
    stake: float
    model_p: float
    won: bool
    commission: float
    closing_odds: float | None = None

    @property
    def profit(self) -> float:
        if self.won:
            return self.stake * (self.odds - 1.0) * (1.0 - self.commission)
        return -self.stake


@dataclass
class BacktestResult:
    bets: list[BacktestBet] = field(default_factory=list)
    predictions: list[float] = field(default_factory=list)
    outcomes: list[int] = field(default_factory=list)
    markets_seen: int = 0

    def summary(self) -> dict:
        n = len(self.bets)
        turnover = sum(b.stake for b in self.bets)
        pnl = sum(b.profit for b in self.bets)
        # Equity curve for drawdown.
        equity, peak, max_dd = 0.0, 0.0, 0.0
        daily_profits: list[float] = []
        for b in self.bets:
            equity += b.profit
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
            daily_profits.append(b.profit)
        mean = pnl / n if n else 0.0
        var = sum((p - mean) ** 2 for p in daily_profits) / n if n else 0.0
        sharpe_like = mean / math.sqrt(var) * math.sqrt(252) if var > 0 else 0.0
        with_close = [b for b in self.bets if b.closing_odds and b.closing_odds > 1.0]
        clv = (
            sum(b.odds / b.closing_odds - 1.0 for b in with_close) / len(with_close)
            if with_close
            else None
        )
        return {
            "markets_seen": self.markets_seen,
            "bets": n,
            "turnover": turnover,
            "pnl": pnl,
            "return_on_turnover": pnl / turnover if turnover else 0.0,
            "max_drawdown": max_dd,
            "sharpe_like": sharpe_like,
            "log_loss": log_loss(self.predictions, self.outcomes),
            "brier": brier_score(self.predictions, self.outcomes),
            "calibration": calibration_bins(self.predictions, self.outcomes),
            "closing_line_value": clv,
            "by_odds_band": self._by_band(),
            "by_sport": self._by_sport(),
        }

    def _by_band(self) -> dict[str, dict]:
        bands = [(1.0, 2.0), (2.0, 3.5), (3.5, 6.0), (6.0, 12.0), (12.0, 1000.0)]
        out = {}
        for lo, hi in bands:
            rows = [b for b in self.bets if lo <= b.odds < hi]
            if rows:
                stake = sum(b.stake for b in rows)
                out[f"{lo}-{hi}"] = {
                    "bets": len(rows),
                    "roi": sum(b.profit for b in rows) / stake if stake else 0.0,
                }
        return out

    def _by_sport(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for b in self.bets:
            row = out.setdefault(b.sport, {"bets": 0, "pnl": 0.0, "stake": 0.0})
            row["bets"] += 1
            row["pnl"] += b.profit
            row["stake"] += b.stake
        for row in out.values():
            row["roi"] = row["pnl"] / row["stake"] if row["stake"] else 0.0
        return out


def run_backtest(
    pipeline: DecisionPipeline,
    risk: RiskEngine,
    replay: Iterable[tuple[MarketSnapshot, dict[int, int], dict[int, float] | None]],
    slippage_ticks: float = 0.01,
    retrain: Callable[[MarketSnapshot], None] | None = None,
) -> BacktestResult:
    """Replay snapshots chronologically.

    replay yields (snapshot, outcomes, closing_odds) where outcomes maps
    selection_id -> 1/0 and closing_odds maps selection_id -> last pre-event
    price (for CLV). Snapshots must be point-in-time: the pipeline only ever
    sees what was knowable at that moment.
    """
    result = BacktestResult()
    commission = pipeline.cfg.betfair.commission_rate

    for snapshot, outcomes, closing in replay:
        if retrain is not None:
            retrain(snapshot)  # walk-forward: only past data may enter the model
        result.markets_seen += 1

        for selection_id, est in pipeline.estimate_market(snapshot).items():
            if selection_id in outcomes:
                result.predictions.append(est.probability)
                result.outcomes.append(outcomes[selection_id])

        ranked, _ = pipeline.evaluate_market(snapshot, now=snapshot.captured_at)
        for opp in ranked:
            approved, _ = risk.approve(opp, now=snapshot.captured_at)
            if not approved:
                continue
            stake = risk.calculate_stake(opp)
            if stake <= 0:
                continue
            fill_odds = max(1.01, opp.odds * (1.0 - slippage_ticks))
            bet = BacktestBet(
                market_id=snapshot.market_id,
                selection_id=opp.selection_id,
                sport=snapshot.sport.value,
                odds=fill_odds,
                stake=stake,
                model_p=opp.estimate.probability,
                won=bool(outcomes.get(opp.selection_id, 0)),
                commission=commission,
                closing_odds=(closing or {}).get(opp.selection_id),
            )
            risk.commit(opp, stake, now=snapshot.captured_at)
            risk.ledger.settle(
                snapshot.event_id, snapshot.sport.value, stake, bet.profit,
                snapshot.captured_at.date(),
            )
            result.bets.append(bet)

    return result
