# Betfair Daily Research-and-Bet Bot

Scans every suitable Betfair market each day, researches each event from
multiple sources, estimates fair probabilities, compares them with executable
exchange prices and places only bets with a statistically validated edge.

**It does not bet on the most likely winner.** A 75% chance is a poor bet when
the price implies 82%. Every decision is driven by commission-adjusted
expected value tested at the *lower confidence bound* of the model estimate.

**The most important rule:** the bot is allowed to conclude *"there are no
qualifying bets today."* Scanning thousands of runners and placing two, three
or zero bets is normal, correct behaviour.

## Architecture

```
Betfair Market Scanner (listMarketCatalogue, 04:00 daily)
        │
        ├── Historical statistics      (sport modules)
        ├── Current form               (sport modules)
        ├── News and injuries          (LLM fact extraction — extract only, never invent)
        ├── Weather and venue          (feature store facts)
        ├── Line-ups, draws, scratches (feature store facts)
        ├── Independent market prices  (market_prior)
        └── Betfair order-book         (prices poller, weight-batched)
                     │
                     ▼
              Feature Store            (timestamped facts, staleness rejection,
                     │                  claim clustering — 5 articles ≠ 5 confirmations)
                     ▼
        Sport probability models       (Dixon–Coles, Elo, margin models, form softmax)
                     │
                     ▼
        Ensemble + calibration         (learned weights, correlation discounting,
                     │                  shrinkage toward market until evidence earned)
                     ▼
        EV + price filter              (commission, lower-bound acceptance test)
                     │
                     ▼
                Risk engine            (fractional Kelly, exposure caps, stop-losses,
                     │                  kill switch, account-discrepancy halt)
                     ▼
        Paper or live execution        (LIMIT orders, idempotent refs, reconciliation)
```

Package map:

| Path | Responsibility |
|---|---|
| `betfair_bot/betfair/` | auth (cert login), JSON-RPC client with request-weight batching (200-point cap), discovery, prices, orders |
| `betfair_bot/research/` | feature store, source-correlation clustering, LLM news extraction, per-sport modules (racing, football, tennis, AFL/NRL) |
| `betfair_bot/modeling/` | ensemble with correlation discounting, market prior (overround removal), calibration + Brier/log-loss tracking |
| `betfair_bot/selection/` | EV math, break-even, minimum-acceptable-odds, opportunity score, automatic rejection rules |
| `betfair_bot/risk/` | fractional Kelly with caps, exposure ledger, daily/weekly stop-loss, kill switch |
| `betfair_bot/execution/` | paper and live executors; final revalidation, price-drift protection, cancel-unmatched, reconciliation, exposure verification |
| `betfair_bot/scheduler/` | daily cycle: 04:00 discovery → 15–60 min recalcs → sport-specific final checkpoints → 22:00 report |
| `betfair_bot/backtest/` | walk-forward replay harness: ROI, drawdown, Sharpe-like, calibration, odds-band/sport breakdowns, closing-line value |
| `betfair_bot/storage/` | SQLite audit trail (markets, snapshots, facts, estimates, opportunities, bets); schema maps 1:1 to production Postgres/Timescale |

## Quick start

```bash
cd betfair-bot
pip install -e ".[dev]"        # core: requests + PyYAML only
pytest                         # 54 tests, no network required

cp .env.example .env           # fill in Betfair credentials
betfair-bot check-config       # validate config + credential presence
betfair-bot scan               # one-off discovery + price snapshot
betfair-bot run                # full daily cycle — PAPER MODE by default
betfair-bot report             # today's report
```

Optional extras: `pip install -e ".[ml]"` (LightGBM/XGBoost for production
models), `".[news]"` (Anthropic client for news fact extraction),
`".[service]"` (FastAPI/Postgres/Redis for the monitored deployment).

## Safety model

- **Paper by default.** Live execution requires `mode: live` in config *and*
  `BETFAIR_LIVE_CONFIRM=YES` in the environment.
- **Fixed, separate bankroll** (`risk.bankroll`) — never account-wide funds.
  Pair with Betfair's own deposit-limit controls.
- One-tenth Kelly, 0.5% max stake, 1% per event, 3% per sport, 5% daily new
  exposure, 2% daily / 5% weekly stop-loss. A sub-minimum stake is refused,
  never rounded up.
- Automatic halt on any unexplained discrepancy between the internal exposure
  ledger and `getAccountFunds`.
- Every order is a LIMIT order with a unique `customerOrderRef` (idempotency),
  unmatched remainder cancelled after a timeout, then reconciled via
  `listCurrentOrders`/`listClearedOrders`.

## Bet acceptance

A selection must survive **all** of:

1. Market open, not in-play, not inside the no-bet window before start.
2. Fresh order book and fresh facts (stale data rejects, never guesses).
3. No unverified material news (a rumoured injury blocks the event until
   officially confirmed or refuted).
4. Confirmed selections/line-ups near the start.
5. Liquidity floor at the executable price.
6. Model confidence ≥ 70%, component disagreement ≤ 8%, training sample ≥ 300.
7. Commission-adjusted EV ≥ 4%.
8. **Lower confidence bound** > break-even + safety margin.
9. Risk engine: stop-losses, exposure caps, kill switch.
10. At execution: price within drift tolerance and above minimum acceptable
    odds, size available, book < 2 minutes old.

Survivors are ranked by the weighted opportunity score (35% EV, 20%
confidence, 15% calibration quality, 10% liquidity, 10% source quality,
5% price stability, 5% completeness) and executed in order.

## The edge engine

Edges come from the pipeline in `betfair_bot/modeling/` that turns raw history
into fitted, calibrated, market-aware probabilities:

1. **Model fitting from data**
   - `dixon_coles.py` — maximum-likelihood attack/defence ratings with
     exponential time decay (recent form counts more) and L2 shrinkage to
     average for thin samples. `betfair-bot fit-football --league E0
     --seasons 2223,2324,2425` fetches football-data.co.uk, fits, reports
     holdout log loss vs the uniform baseline, and saves to
     `data/ratings/football.json` where the bot auto-loads it.
   - `elo_fit.py` — surface-specific tennis Elo with decaying K-factor and
     cross-surface transfer, replayed chronologically (point-in-time safe for
     back-testing by construction).
2. **Learned ensemble weights** — `weight_optimizer.py` fits the component
   weights on the probability simplex by minimising log loss over graded
   history, per sport. It also computes each component's marginal value
   (loss increase when removed) — the automated "does this source still add
   predictive value?" test; `prune_useless_components` flags dead sources.
3. **Fitted calibration** — `logistic_calibration.py` learns
   `p_fair = σ(a·logit(p_model) + b·logit(p_market) + c)` from graded bets:
   `a` shrinks model overconfidence, `b` learns how much the market already
   knows, `c` corrects systematic bias (e.g. longshot bias). Drop-in
   replacement for the bootstrap `ShrinkageCalibrator`; auto-loaded once
   saved.
4. **Order-book intelligence** — `research/orderbook.py` reads the exchange
   itself: back/lay depth imbalance, price momentum from recorded snapshots,
   and visible-depth-scaled confidence. It enters the ensemble as the
   `betfair_order_book` component as a capped ±6% tilt on the market prior —
   steam is information, but the moved price must still clear the EV filter,
   so shortening odds never automatically create a bet.

The intended loop: fit models → run paper mode (accumulates graded
predictions and price history) → refit weights and calibration from that
history → repeat. Every refit is measured by holdout log loss, so the engine
only ever earns trust it can demonstrate.

## Validating edge before real money

1. **Historical back-test** (`betfair_bot/backtest/engine.py`): point-in-time
   replay, walk-forward retraining hook, realistic commission/slippage.
   Judge on log loss, Brier, calibration, return on turnover, drawdown,
   odds-band and sport breakdowns, and closing-line value.
2. **Shadow mode (8–12 weeks):** run `mode: paper` against live markets. Every
   proposed bet is recorded with the actual available price and graded, and
   CLV is tracked — repeatedly beating the close is the leading indicator of
   real edge even through a losing sample.
3. **Small live bankroll:** one or two sports, tiny stakes, no in-play,
   `betfair-bot report` daily, immediate rollback if calibration deteriorates
   (`PerformanceTracker.report()`).

The ensemble weights in `config/default.yaml` are initial priors only —
back-testing must re-optimise them per sport and regularly re-test whether
each source still adds predictive value. Until live evidence accumulates, the
`ShrinkageCalibrator` pulls estimates toward the market, which deliberately
suppresses betting early on.

## Betfair API notes

- Certificate (non-interactive) login for unattended operation; keep-alive
  every 15 minutes; automatic re-login on session expiry.
- `listMarketBook` calls are batched so the aggregate request weight stays
  under Betfair's 200-point cap (`EX_BEST_OFFERS` + `EX_TRADED` = 22/market
  → 9 markets per call).
- `turnInPlayEnabled` is captured at discovery so in-play behaviour is known
  before any order is considered (in-play betting is disabled in Phase 1).
- Credentials and certificates come from environment variables / a secrets
  manager — never from config files or the repository.

## Build order

- **Phase 1 (this code):** discovery, order-book capture, feature store,
  football + racing models, ensemble/EV/risk engines, paper betting, daily
  report, back-test harness.
- **Phase 2:** Stream API prices, order-management hardening, Telegram/SMS
  alerts, Grafana/OpenTelemetry, Postgres/Timescale migration.
- **Phase 3:** tennis, AFL, NRL, cricket production models; portfolio-level
  allocation.
- **Phase 4:** source-contribution analysis, market-regime detection,
  automated retraining, champion/challenger, news-impact learning,
  closing-price optimisation.
