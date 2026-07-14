# Betfair Research-and-Bet Bot — project memory

You are working on Ken Armitt's Betfair betting bot (Digital One Agency,
ken@digitaloneagency.com.au). Built originally in a Claude Code cloud session;
this file is the handoff so any local session continues seamlessly.

## People

- **Ken** — owner, runs this on his Windows PC (WSL Ubuntu). Betfair AU
  account is in his name. Prefers you to drive: run commands yourself and ask
  approval rather than giving him instructions to type.
- **Charlie** (charliezdotcom@gmail.com) — collaborator, to be invited to the
  GitHub repo with Write access.

## What this is

A daily research-and-bet bot for Betfair Exchange (betfair.com.au account).
It scans every suitable market daily, researches events, estimates fair
probabilities, and ONLY bets when commission-adjusted EV clears a floor at
the lower confidence bound. It must never bet on "most likely winner" —
value only. "No qualifying bets today" is a correct outcome. Full details in
README.md — read it before doing anything.

## Current status (update this as you go)

- [x] Code complete: pipeline, edge engine, risk engine, execution, 84 tests
- [x] Betfair AU account created, KYC verified (username set by Ken)
- [ ] `betfair-bot setup-keys` run (generates certs + app keys + .env)
- [ ] Certificate uploaded to Betfair (My Account → Security → Automated
      Betting Program Access → paste certs/client-2048.crt)
- [ ] Live app key activation requested (email api@betfair.com.au — delayed
      key works immediately for paper mode; live key = real-time prices)
- [ ] First `betfair-bot scan` successful
- [ ] Football ratings fitted (`betfair-bot fit-football --league E0 --seasons 2223,2324,2425`)
- [ ] Paper mode running continuously (`betfair-bot run`)
- [ ] Standalone GitHub repo D1AgencyMAX/betfair-bot created + code pushed
      (currently code lives on d1-dashboard branch claude/betfair-research-bet-bot-rv41ra)
- [ ] Charlie invited as collaborator
- [ ] Back-test on historical data (loader not yet built)
- [ ] 8–12 weeks shadow mode with closing-line value tracking
- [ ] Live with small bankroll (ONLY after all the above)

## Hard safety rules — do not bend these

1. **Paper mode is the default.** Live execution requires `mode: live` in
   config AND `BETFAIR_LIVE_CONFIRM=YES` in env. Never set these yourself;
   only Ken does, deliberately, after backtest + shadow validation.
2. **No deposits.** Never suggest funding the account until Stage 3
   (validated edge). If Betfair requires a small deposit for live-key
   activation, Ken decides.
3. Credentials live in `.env` (gitignored) and nowhere else. Never commit
   keys, certs, or passwords. certs/ must stay chmod 600.
4. The risk limits in config/default.yaml (0.5% stake, stop-losses, exposure
   caps) are load-bearing. Don't raise them; question anyone who asks.

## Common commands

```bash
python3 -m pip install -e ".[dev]"   # install (WSL: apt install python3-pip openssl first)
python3 -m pytest tests/ -q          # 84 tests, offline, ~8s
betfair-bot check-config             # validate config + credential presence
betfair-bot setup-keys               # certs + app keys + .env bootstrap
betfair-bot scan                     # one-off market discovery
betfair-bot run                      # full daily cycle (paper mode)
betfair-bot report                   # today's summary
betfair-bot fit-football --league E0 --seasons 2223,2324,2425
```

## Architecture in one breath

`scheduler/daily_cycle.py` (04:00 discovery → recalcs → pre-jump checkpoints)
→ `research/` modules + feature store (timestamped facts, staleness, claim
clustering) → `modeling/` ensemble (learned weights, correlation discounting,
calibration) → `selection/` EV filter (per-market commission, lower-bound
test, spread gate) → `risk/` (fractional Kelly, exposure ledger, stop-losses,
kill switch) → `execution/` (paper or live LIMIT orders, idempotent refs,
reconciliation). Backtest harness in `backtest/engine.py` runs the same
pipeline. Costs modelled: Market Base Rate per market, premium charge,
tick-ladder slippage, spread.

## Next steps (in order)

1. Run setup-keys with Ken; walk him through the cert upload; draft the
   live-key email.
2. Verify with check-config + scan (delayed key is fine).
3. Fit football ratings; start `betfair-bot run` in paper mode.
4. Split code to its own repo D1AgencyMAX/betfair-bot once Ken creates it
   on github.com/new (Private), invite Charlie, then archive the
   d1-dashboard branch.
5. Build the free-data backtest loader (Betfair BSP files at
   promo.betfair.com/betfairsp + Automation Hub CSVs) and run Stage-1
   validation. Racing form needs Punting Form API (AU$59/mo) — Ken decides.
