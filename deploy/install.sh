#!/usr/bin/env bash
# One-shot installer for the WhatsApp AI comedian.
#
# Defaults (safe for any VPS that already runs something on :80/:443):
#   - Installs Docker if missing
#   - Clones into /opt/comedian
#   - Runs app-only on 127.0.0.1:${APP_PORT:-3100}
#   - You then point your existing nginx/Caddy at that port
#
# Add --with-caddy on a greenfield VPS to also spin up Caddy on :80/:443.
#
# Usage on the VPS itself (as root or with sudo):
#   curl -fsSL https://raw.githubusercontent.com/D1AgencyMAX/d1-dashboard/claude/ai-prank-call-comedian-RpBI6/deploy/install.sh \
#     | sudo bash
#
#   # or with a flag:
#   curl -fsSL .../install.sh | sudo bash -s -- --with-caddy

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/D1AgencyMAX/d1-dashboard.git}"
BRANCH="${BRANCH:-claude/ai-prank-call-comedian-RpBI6}"
INSTALL_DIR="${INSTALL_DIR:-/opt/comedian}"
WITH_CADDY=0

for arg in "$@"; do
    case "$arg" in
        --with-caddy) WITH_CADDY=1 ;;
        --app-only)   WITH_CADDY=0 ;;
        *)            echo "Unknown flag: $arg" >&2; exit 2 ;;
    esac
done

log() { printf "\n\033[1;36m[install]\033[0m %s\n" "$*"; }
warn() { printf "\n\033[1;33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\n\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run me with sudo or as root."
command -v apt-get >/dev/null || die "This installer expects a Debian/Ubuntu host (apt-get)."

# Detect whether :80/:443 is already in use. Bail into app-only if so.
if [ "$WITH_CADDY" -eq 1 ] && command -v ss >/dev/null; then
    if ss -ltn '( sport = :80 or sport = :443 )' 2>/dev/null | grep -q LISTEN; then
        warn ":80 or :443 is already listening. Forcing --app-only to avoid collision."
        WITH_CADDY=0
    fi
fi

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

command -v git >/dev/null || apt-get install -y git

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

# Local bind for the app container. Default keeps it off the public internet
# so your existing reverse proxy (nginx/Caddy) is the only thing exposed.
APP_BIND=127.0.0.1
APP_PORT=3100

# Only used when you run with docker-compose.edge.yml (--with-caddy):
APP_HOSTNAME=
EOF
    echo
    echo "=============================================================="
    echo "  Edit $INSTALL_DIR/.env with real keys, then re-run:"
    echo "    cd $INSTALL_DIR && sudo bash deploy/install.sh"
    if [ "$WITH_CADDY" -eq 1 ]; then
        echo "  (using --with-caddy — set APP_HOSTNAME in .env too)"
    fi
    echo "=============================================================="
    exit 0
fi

if [ "$WITH_CADDY" -eq 1 ]; then
    if ! grep -qE '^APP_HOSTNAME=[^[:space:]]+' .env; then
        die "APP_HOSTNAME is empty in .env (required for --with-caddy). Set it and re-run."
    fi
    if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
        log "Opening ports 80 + 443 (ufw)."
        ufw allow 80/tcp || true
        ufw allow 443/tcp || true
    fi
    log "Building + starting stack (app + Caddy)."
    docker compose -f docker-compose.yml -f docker-compose.edge.yml up -d --build
else
    log "Building + starting app-only stack on 127.0.0.1:$(grep -E '^APP_PORT=' .env | cut -d= -f2 || echo 3100)."
    docker compose up -d --build
fi

sleep 5
docker compose ps

if [ "$WITH_CADDY" -eq 1 ]; then
    log "Visit: https://$(grep -E '^APP_HOSTNAME=' .env | cut -d= -f2)"
else
    APP_PORT_VAL=$(grep -E '^APP_PORT=' .env | cut -d= -f2 || echo 3100)
    log "App listening on 127.0.0.1:${APP_PORT_VAL}"
    log "Point your existing reverse proxy at that port. Snippets:"
    log "  $INSTALL_DIR/deploy/proxy-snippets/nginx-vhost.conf.example"
    log "  $INSTALL_DIR/deploy/proxy-snippets/Caddyfile.snippet"
fi

log "Tail logs:  docker compose logs -f --tail=100"
