"""Configuration loading and typed access.

Credentials never live in config files; they are read from the environment
(or a secrets manager mounted into the environment) at runtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"


@dataclass
class RiskConfig:
    bankroll: float = 1000.0
    kelly_fraction: float = 0.10
    maximum_stake_bankroll_pct: float = 0.005
    maximum_event_exposure_pct: float = 0.01
    maximum_sport_exposure_pct: float = 0.03
    maximum_daily_new_exposure_pct: float = 0.05
    daily_stop_loss_pct: float = 0.02
    weekly_stop_loss_pct: float = 0.05
    min_stake: float = 5.0


@dataclass
class SelectionConfig:
    minimum_expected_value: float = 0.04
    minimum_model_confidence: float = 0.70
    safety_margin: float = 0.01
    max_price_drift_pct: float = 0.05
    max_spread_ticks: int = 5
    min_available_liquidity: float = 200.0
    min_historical_sample: int = 300
    max_model_disagreement: float = 0.08
    min_seconds_before_start: float = 45.0
    opportunity_score_weights: dict[str, float] = field(default_factory=lambda: {
        "expected_value": 0.35,
        "model_confidence": 0.20,
        "calibration_quality": 0.15,
        "market_liquidity": 0.10,
        "source_quality": 0.10,
        "price_stability": 0.05,
        "data_completeness": 0.05,
    })


@dataclass
class BetfairConfig:
    login: str = "certificate"
    endpoint: str = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    identity_endpoint: str = "https://identitysso-cert.betfair.com/api/certlogin"
    keep_alive_endpoint: str = "https://identitysso.betfair.com/api/keepAlive"
    keep_alive_minutes: int = 15
    commission_rate: float = 0.05      # fallback only; per-market MBR wins
    premium_charge_rate: float = 0.0   # long-run haircut once consistently winning
    max_request_weight: int = 200
    price_poll_seconds: int = 60

    @property
    def app_key(self) -> str:
        return os.environ.get("BETFAIR_APP_KEY", "")

    @property
    def username(self) -> str:
        return os.environ.get("BETFAIR_USERNAME", "")

    @property
    def password(self) -> str:
        return os.environ.get("BETFAIR_PASSWORD", "")

    @property
    def cert_file(self) -> str:
        return os.environ.get("BETFAIR_CERT_FILE", "")

    @property
    def key_file(self) -> str:
        return os.environ.get("BETFAIR_KEY_FILE", "")


@dataclass
class BotConfig:
    mode: str = "paper"
    timezone: str = "Australia/Sydney"
    betfair: BetfairConfig = field(default_factory=BetfairConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    ensemble_weights: dict[str, float] = field(default_factory=dict)
    discovery: dict[str, Any] = field(default_factory=dict)
    research: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)
    storage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def live_enabled(self) -> bool:
        """Live execution requires both config intent and an explicit env confirmation."""
        return self.mode == "live" and os.environ.get("BETFAIR_LIVE_CONFIRM") == "YES"


def _apply(dc: Any, data: dict[str, Any]) -> None:
    for key, value in (data or {}).items():
        if hasattr(dc, key) and not isinstance(getattr(type(dc), key, None), property):
            setattr(dc, key, value)


def load_config(path: str | Path | None = None) -> BotConfig:
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(path) as fh:
        raw = yaml.safe_load(fh) or {}

    cfg = BotConfig(raw=raw)
    cfg.mode = raw.get("mode", cfg.mode)
    cfg.timezone = raw.get("timezone", cfg.timezone)
    _apply(cfg.betfair, raw.get("betfair", {}))
    _apply(cfg.risk, raw.get("risk", {}))
    _apply(cfg.selection, raw.get("selection", {}))
    cfg.ensemble_weights = raw.get("ensemble_weights", {})
    cfg.discovery = raw.get("discovery", {})
    cfg.research = raw.get("research", {})
    cfg.execution = raw.get("execution", {})
    cfg.storage = raw.get("storage", {})
    return cfg
