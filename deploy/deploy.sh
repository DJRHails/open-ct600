#!/usr/bin/env bash
# Deploy the public site on bonbon behind the shared host Caddy (https://open-ct600.hails.info).
#
# Pulls the image CI pushed to GHCR (.github/workflows/deploy.yml), starts it, waits for its
# health check, then publishes the Caddy fragment and reloads Caddy. Idempotent and safe to
# re-run.
#
# Usage:
#   TAG=sha-<12 hex> COMPANIES_HOUSE_API_KEY=... deploy/deploy.sh
#
# Env:
#   TAG                      image tag to deploy (default: latest)
#   COMPANIES_HOUSE_API_KEY  the Companies House public data API key (required)
#   CADDY_SITES              host caddy sites dir (default: /home/d/projects/caddy/sites)
#   CADDY_CONTAINER          caddy container name (default: caddy)
set -euo pipefail

cd "$(dirname "$0")"

readonly TAG="${TAG:-latest}"
readonly CADDY_SITES="${CADDY_SITES:-/home/d/projects/caddy/sites}"
readonly CADDY_CONTAINER="${CADDY_CONTAINER:-caddy}"
readonly CADDY_FRAGMENT="open-ct600.hails.info.Caddyfile"
readonly SERVICE="open-ct600-web"
readonly HEALTH_TIMEOUT=120

log() { printf '==> %s\n' "$*"; }
die() {
  echo "deploy.sh: $*" >&2
  exit 1
}

case "${1:-}" in
"") ;;
-h | --help)
  sed -n '2,15p' "$0"
  exit 0
  ;;
*) die "unknown argument: $1" ;;
esac

command -v docker >/dev/null || die "docker not found"
docker network inspect caddy >/dev/null 2>&1 ||
  die "external docker network 'caddy' not found (docker network create caddy)"
[[ -d "$CADDY_SITES" ]] || die "caddy sites dir not found: $CADDY_SITES"
[[ -n "${COMPANIES_HOUSE_API_KEY:-}" ]] ||
  die "COMPANIES_HOUSE_API_KEY is not set (the repo's Actions secret of that name)"

export TAG COMPANIES_HOUSE_API_KEY
log "Pulling image (TAG=$TAG)"
docker compose pull

log "Starting $SERVICE"
docker compose up -d --remove-orphans

cid=$(docker compose ps -q "$SERVICE")
[[ -n "$cid" ]] || die "no container for $SERVICE"
log "Waiting for $SERVICE to become healthy (timeout ${HEALTH_TIMEOUT}s)"
elapsed=0
while true; do
  status=$(docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo unknown)
  [[ "$status" == healthy ]] && break
  if [[ "$status" == unhealthy ]] || ((elapsed >= HEALTH_TIMEOUT)); then
    docker logs --tail 60 "$cid" >&2 || true
    die "$SERVICE did not become healthy (last status: $status)"
  fi
  sleep 5
  elapsed=$((elapsed + 5))
done
log "$SERVICE is healthy"

log "Installing Caddy fragment -> $CADDY_SITES/$CADDY_FRAGMENT"
cp "$CADDY_FRAGMENT" "$CADDY_SITES/$CADDY_FRAGMENT"
docker exec "$CADDY_CONTAINER" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

log "Deploy complete: https://open-ct600.hails.info"
