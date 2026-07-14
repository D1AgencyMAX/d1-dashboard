"""One-command post-signup setup: certificates, app keys, .env.

Everything after account creation is automatable:

    betfair-bot setup-keys

1. Generates the self-signed client certificate pair Betfair requires for
   non-interactive (bot) login, with correct permissions.
2. Logs in interactively with BETFAIR_USERNAME/BETFAIR_PASSWORD and creates
   (or fetches) the developer application keys via the Accounts API.
3. Writes a ready-to-fill .env and prints the two manual steps that only the
   account holder can do on the website (cert upload, live-key activation).

The account itself (and its KYC) must be created by the account holder on
betfair.com.au — that part cannot and should not be automated.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import requests

IDENTITY_LOGIN = "https://identitysso.betfair.com/api/login"
ACCOUNT_ENDPOINT = "https://api.betfair.com/exchange/account/json-rpc/v1"

CERT_UPLOAD_HELP = (
    "Upload the certificate in Betfair account security settings\n"
    "  (My Account -> Security -> Automated Betting Program Access -> Edit,\n"
    "   paste the contents of client-2048.crt). AU help: betfair.com.au support\n"
    "   article 'Certificate login'."
)


def generate_certificates(cert_dir: Path) -> tuple[Path, Path]:
    """Create the RSA key + self-signed cert pair for Betfair cert login."""
    cert_dir.mkdir(parents=True, exist_ok=True)
    key_file = cert_dir / "client-2048.key"
    crt_file = cert_dir / "client-2048.crt"
    if key_file.exists() and crt_file.exists():
        print(f"Certificates already exist in {cert_dir}, keeping them.")
        return crt_file, key_file
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(key_file), "-out", str(crt_file),
            "-days", "3650", "-nodes",
            "-subj", "/C=AU/O=BetfairBot/CN=betfair-bot-client",
        ],
        check=True,
        capture_output=True,
    )
    for f in (key_file, crt_file):
        os.chmod(f, stat.S_IRUSR | stat.S_IWUSR)  # 600 — private material
    print(f"Generated {crt_file} and {key_file} (chmod 600).")
    return crt_file, key_file


def interactive_session_token(username: str, password: str) -> str:
    """Bootstrap login used only for key management (no app key needed yet)."""
    resp = requests.post(
        IDENTITY_LOGIN,
        data={"username": username, "password": password},
        headers={"X-Application": "keysetup", "Accept": "application/json"},
        timeout=20,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("status") != "SUCCESS":
        raise RuntimeError(
            f"Login failed: {body.get('status')} {body.get('error')} — "
            "check credentials; TWO_FACTOR/strong-auth accounts must log in "
            "on the website first or use an app password."
        )
    return body["token"]


def _account_rpc(method: str, params: dict, session_token: str) -> dict:
    resp = requests.post(
        ACCOUNT_ENDPOINT,
        json={
            "jsonrpc": "2.0",
            "method": f"AccountAPING/v1.0/{method}",
            "params": params,
            "id": 1,
        },
        headers={
            "X-Authentication": session_token,
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RuntimeError(f"{method} failed: {body['error']}")
    return body["result"]


def get_or_create_app_keys(session_token: str, app_name: str) -> list[dict]:
    """Fetch existing developer app keys, creating them if none exist.

    createDeveloperAppKeys returns one application with two versions: the
    delayed key (active immediately, lagged prices, no orders) and the live
    key (requires activation by Betfair before it works).
    """
    existing = _account_rpc("getDeveloperAppKeys", {}, session_token)
    if existing:
        return existing
    created = _account_rpc(
        "createDeveloperAppKeys", {"appName": app_name}, session_token
    )
    return [created]


def summarise_keys(apps: list[dict]) -> list[dict]:
    keys = []
    for app in apps:
        for version in app.get("appVersions", []):
            keys.append({
                "app_name": app.get("appName", ""),
                "key": version.get("applicationKey", ""),
                "delayed": bool(version.get("delayData", False)),
                "active": bool(version.get("active", False)),
            })
    return keys


def write_env(
    env_path: Path,
    username: str,
    app_key: str,
    crt_file: Path,
    key_file: Path,
) -> None:
    if env_path.exists():
        print(f"{env_path} already exists — not overwriting. Values to set:")
        print(f"  BETFAIR_APP_KEY={app_key}")
        print(f"  BETFAIR_CERT_FILE={crt_file}")
        print(f"  BETFAIR_KEY_FILE={key_file}")
        return
    env_path.write_text(
        f"BETFAIR_APP_KEY={app_key}\n"
        f"BETFAIR_USERNAME={username}\n"
        "BETFAIR_PASSWORD=\n"
        f"BETFAIR_CERT_FILE={crt_file}\n"
        f"BETFAIR_KEY_FILE={key_file}\n"
        "# BETFAIR_LIVE_CONFIRM=YES   # only when going live, deliberately\n"
    )
    os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
    print(f"Wrote {env_path} (fill in BETFAIR_PASSWORD yourself).")


def run_setup(cert_dir: str = "certs", app_name: str = "d1-betfair-bot") -> int:
    username = os.environ.get("BETFAIR_USERNAME", "")
    password = os.environ.get("BETFAIR_PASSWORD", "")

    crt_file, key_file = generate_certificates(Path(cert_dir))

    if not (username and password):
        print(
            "\nSet BETFAIR_USERNAME and BETFAIR_PASSWORD to also create app "
            "keys, e.g.:\n"
            "  BETFAIR_USERNAME=... BETFAIR_PASSWORD=... betfair-bot setup-keys\n"
        )
        print(CERT_UPLOAD_HELP)
        return 0

    token = interactive_session_token(username, password)
    keys = summarise_keys(get_or_create_app_keys(token, app_name))
    print("\nApplication keys:")
    delayed_key = ""
    for k in keys:
        kind = "DELAYED (free, use for paper mode)" if k["delayed"] else "LIVE"
        state = "active" if k["active"] else "NOT ACTIVE — request activation from Betfair"
        print(f"  {k['key']}  [{kind}] [{state}]")
        if k["delayed"]:
            delayed_key = k["key"]

    write_env(Path(".env"), username, delayed_key or keys[0]["key"], crt_file, key_file)

    print("\nRemaining manual steps (account holder only):")
    print(f"1. {CERT_UPLOAD_HELP}")
    print("2. When ready for live orders: ask Betfair (AU: automation team /")
    print("   api@betfair.com.au) to activate the LIVE key — free for AU customers.")
    print("3. Verify with: betfair-bot check-config && betfair-bot scan")
    return 0
