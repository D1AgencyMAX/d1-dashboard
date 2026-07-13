"""Betfair Exchange API JSON-RPC client.

Handles certificate (non-interactive) login, keep-alive, and request-weight
budgeting. Betfair caps the aggregate data-request weight at 200 points per
listMarketBook/listMarketCatalogue-style call, so price polling must batch
market ids to stay under the cap.
"""

from __future__ import annotations

import itertools
import logging
import threading
import time
from typing import Any, Iterable, Iterator

import requests

from ..config import BetfairConfig

log = logging.getLogger(__name__)

# Price-projection weights per market for listMarketBook (Betfair docs).
PRICE_DATA_WEIGHTS = {
    None: 2,
    "SP_AVAILABLE": 3,
    "SP_TRADED": 7,
    "EX_BEST_OFFERS": 5,
    "EX_ALL_OFFERS": 17,
    "EX_TRADED": 17,
}


class BetfairError(RuntimeError):
    def __init__(self, message: str, code: Any = None, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class BetfairClient:
    """Thin, synchronous JSON-RPC client with session management."""

    def __init__(self, cfg: BetfairConfig):
        self.cfg = cfg
        self._session_token: str | None = None
        self._session_ts: float = 0.0
        self._lock = threading.Lock()
        self._http = requests.Session()
        self.healthy: bool = False

    # ------------------------------------------------------------------ auth

    def login(self) -> None:
        """Certificate login for unattended bots (identitysso-cert)."""
        if not self.cfg.app_key:
            raise BetfairError("BETFAIR_APP_KEY is not set")
        if self.cfg.login == "certificate":
            if not (self.cfg.cert_file and self.cfg.key_file):
                raise BetfairError("BETFAIR_CERT_FILE / BETFAIR_KEY_FILE not set for certificate login")
            resp = self._http.post(
                self.cfg.identity_endpoint,
                data={"username": self.cfg.username, "password": self.cfg.password},
                cert=(self.cfg.cert_file, self.cfg.key_file),
                headers={"X-Application": self.cfg.app_key},
                timeout=20,
            )
            resp.raise_for_status()
            body = resp.json()
            if body.get("loginStatus") != "SUCCESS":
                raise BetfairError(f"Betfair login failed: {body.get('loginStatus')}")
            self._session_token = body["sessionToken"]
        else:
            resp = self._http.post(
                "https://identitysso.betfair.com/api/login",
                data={"username": self.cfg.username, "password": self.cfg.password},
                headers={
                    "X-Application": self.cfg.app_key,
                    "Accept": "application/json",
                },
                timeout=20,
            )
            resp.raise_for_status()
            body = resp.json()
            if body.get("status") != "SUCCESS":
                raise BetfairError(f"Betfair login failed: {body.get('status')} {body.get('error')}")
            self._session_token = body["token"]
        self._session_ts = time.time()
        self.healthy = True
        log.info("Betfair login OK (%s)", self.cfg.login)

    def keep_alive(self) -> None:
        if not self._session_token:
            return
        resp = self._http.post(
            self.cfg.keep_alive_endpoint,
            headers={
                "X-Application": self.cfg.app_key,
                "X-Authentication": self._session_token,
                "Accept": "application/json",
            },
            timeout=20,
        )
        ok = resp.ok and resp.json().get("status") == "SUCCESS"
        self.healthy = bool(ok)
        if ok:
            self._session_ts = time.time()
        else:
            log.warning("keepAlive failed; will re-login on next call")
            self._session_token = None

    def ensure_session(self) -> None:
        with self._lock:
            if not self._session_token:
                self.login()
            elif time.time() - self._session_ts > self.cfg.keep_alive_minutes * 60:
                try:
                    self.keep_alive()
                except requests.RequestException:
                    self._session_token = None
                if not self._session_token:
                    self.login()

    # --------------------------------------------------------------- rpc core

    def call(self, method: str, params: dict[str, Any]) -> Any:
        """Invoke a SportsAPING method, retrying once on session expiry."""
        self.ensure_session()
        payload = {
            "jsonrpc": "2.0",
            "method": f"SportsAPING/v1.0/{method}",
            "params": params,
            "id": 1,
        }
        for attempt in (1, 2):
            try:
                resp = self._http.post(
                    self.cfg.endpoint,
                    json=payload,
                    headers={
                        "X-Application": self.cfg.app_key,
                        "X-Authentication": self._session_token or "",
                        "Content-Type": "application/json",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                body = resp.json()
            except requests.RequestException as exc:
                self.healthy = False
                if attempt == 2:
                    raise BetfairError(f"{method} transport error: {exc}") from exc
                time.sleep(1.0)
                continue

            if "error" in body:
                err = body["error"]
                api_code = (
                    (err.get("data") or {}).get("APINGException", {}).get("errorCode")
                )
                if api_code in ("INVALID_SESSION_INFORMATION", "NO_SESSION") and attempt == 1:
                    log.info("Session expired; re-authenticating")
                    with self._lock:
                        self._session_token = None
                    self.ensure_session()
                    continue
                self.healthy = api_code not in ("SERVICE_BUSY", "TIMEOUT_ERROR")
                raise BetfairError(f"{method} failed: {api_code or err}", code=api_code, data=err)

            self.healthy = True
            return body["result"]
        raise BetfairError(f"{method}: retries exhausted")

    # ------------------------------------------------------------- weighting

    def market_book_batch_size(self, price_data: Iterable[str]) -> int:
        """Max markets per listMarketBook call under the aggregate weight cap."""
        weight = sum(PRICE_DATA_WEIGHTS.get(p, 17) for p in price_data) or PRICE_DATA_WEIGHTS[None]
        return max(1, self.cfg.max_request_weight // weight)

    @staticmethod
    def chunked(items: list[Any], size: int) -> Iterator[list[Any]]:
        it = iter(items)
        while chunk := list(itertools.islice(it, size)):
            yield chunk
