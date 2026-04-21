#!/usr/bin/env bash
# One-shot installer for the WhatsApp AI comedian on a fresh Debian/Ubuntu VPS.
# Run as root (or with sudo) on VPS 2:
#   curl -fsSL https://raw.githubusercontent.com/D1AgencyMAX/d1-dashboard/claude/ai-prank-call-comedian-RpBI6/deploy/install.sh | sudo bash
# ...or clone the repo and run: sudo bash deploy/install.sh
#
# The script:
#   1. Installs Docker + docker-compose-plugin if missing.
#   2. Clones the repo into /opt/comedian (or pulls latest if present).
#   3. Copies .env.example to .env if there's no .env yet; pauses for edits.
#   4. Opens ports 80 + 443 (ufw) if ufw is active.
#   5. Builds + starts the stack with docker compose.

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/D1AgencyMAX/d1-dashboard.git}"
BRANCH="${BRANCH:-claude/ai-prank-call-comedian-RpBI6}"
INSTALL_DIR="${INSTALL_DIR:-/opt/comedian}"

log() { printf "\n\033[1;36m[install]\033[0m %s\n" "$*"; }
die() { printf "\n\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run me with sudo or as root."
command -v apt-get >/dev/null || die "This installer expects a Debian/Ubuntu host (apt-get)."

log "Updating apt caches."
apt-get update -y

if ! command -v docker >/dev/null; then
    log "Installing Docker Engine."
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc 2>/dev/null \
        || curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    . /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    log "Docker present: $(docker --version)"
fi

if ! command -v git >/dev/null; then
    log "Installing git."
    apt-get install -y git
fi

if [ ! -d "$INSTALL_DIR/.git" ]; then
    log "Cloning $REPO_URL#$BRANCH into $INSTALL_DIR"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
else
    log "Updating existing checkout at $INSTALL_DIR"
    git -C "$INSTALL_DIR" fetch origin "$BRANCH"
    git -C "$INSTALL_DIR" checkout "$BRANCH"
    git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
fi

cd "$INSTALL_DIR"

if [ ! -f .env ]; then
    log "Creating .env from .env.example — edit it before continuing."
    cp .env.example .env
    cat >> .env <<'EOF'

# Public hostname Caddy should serve HTTPS on.
# Examples:
#   APP_HOSTNAME=comedian.yourdomain.com
#   APP_HOSTNAME=50-6-251-57.nip.io
APP_HOSTNAME=
EOF
    echo
    echo "=============================================================="
    echo "  Edit $INSTALL_DIR/.env with real keys and APP_HOSTNAME, then"
    echo "  re-run:  cd $INSTALL_DIR && docker compose up -d --build"
    echo "=============================================================="
    exit 0
fi

if [ -z "${APP_HOSTNAME:-$(grep -E '^APP_HOSTNAME=' .env | cut -d= -f2)}" ]; then
    die "APP_HOSTNAME is empty in .env. Set it (e.g. APP_HOSTNAME=comedian.example.com) and re-run."
fi

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    log "Opening ports 80 + 443 (ufw)."
    ufw allow 80/tcp || true
    ufw allow 443/tcp || true
fi

log "Building and starting stack (docker compose up -d --build)."
docker compose up -d --build

log "Waiting 5s for containers to settle."
sleep 5
docker compose ps

log "Done. Visit https://$(grep -E '^APP_HOSTNAME=' .env | cut -d= -f2) in a browser."
log "Tail logs:  docker compose logs -f --tail=100"
