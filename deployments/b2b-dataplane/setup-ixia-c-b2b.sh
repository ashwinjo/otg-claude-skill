#!/usr/bin/env bash
# setup-ixia-c-b2b.sh — Deploy Ixia-c B2B dataplane infrastructure
#
# What this script does:
#   1. Creates veth pair (veth-a <-> veth-z) on host
#   2. Brings up all containers via docker compose
#   3. Waits for traffic engine ports to be ready
#   4. Injects location_map config into controller
#   5. Validates controller is healthy and responds
#
# Usage:
#   sudo ./setup-ixia-c-b2b.sh           # Deploy
#   sudo ./setup-ixia-c-b2b.sh --teardown # Tear down all
#
# Requirements:
#   - Docker with compose plugin
#   - sudo / root privileges (for ip link commands)
#   - Ports 8443 and 40051 free on the host

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose-b2b-dataplane.yml"
CONTROLLER_URL="https://localhost:8443"
TE_A_PORT="5555"
TE_B_PORT="5556"
VETH_A="veth-a"
VETH_Z="veth-z"
CONTROLLER_CONFIG_PATH="/home/ixia-c/controller/config/config.yaml"

# ─── Colours ────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()     { error "$*"; exit 1; }

# ─── Teardown ───────────────────────────────────────────────────────────────
teardown() {
    info "Tearing down Ixia-c B2B deployment..."

    info "Stopping containers..."
    docker compose -f "${COMPOSE_FILE}" down --remove-orphans 2>/dev/null || true

    info "Removing veth pair..."
    if ip link show "${VETH_A}" &>/dev/null; then
        sudo ip link delete "${VETH_A}" 2>/dev/null || true
        info "  Removed ${VETH_A} <-> ${VETH_Z}"
    else
        warn "  veth pair not found — already removed"
    fi

    info "Teardown complete."
}

if [[ "${1:-}" == "--teardown" ]]; then
    teardown
    exit 0
fi

# ─── Step 1: Create veth pair ────────────────────────────────────────────────
info "Step 1: Creating veth pair ${VETH_A} <-> ${VETH_Z}..."

if ip link show "${VETH_A}" &>/dev/null; then
    warn "  veth pair already exists — skipping creation"
else
    sudo ip link add "${VETH_A}" type veth peer name "${VETH_Z}"
    sudo ip link set "${VETH_A}" up
    sudo ip link set "${VETH_Z}" up
    info "  Created and brought up ${VETH_A} <-> ${VETH_Z}"
fi

# ─── Step 2: Start containers ────────────────────────────────────────────────
info "Step 2: Starting containers via docker compose..."
docker compose -f "${COMPOSE_FILE}" up -d

# ─── Step 3: Wait for controller healthcheck ────────────────────────────────
info "Step 3: Waiting for controller to become healthy..."
MAX_WAIT=60
WAITED=0
until docker inspect keng-controller --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; do
    if [[ ${WAITED} -ge ${MAX_WAIT} ]]; then
        error "Controller did not become healthy within ${MAX_WAIT}s"
        docker logs keng-controller --tail=20
        die "Deployment failed at controller healthcheck"
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    info "  ... waiting (${WAITED}s / ${MAX_WAIT}s)"
done
info "  Controller is healthy"

# ─── Step 4: Wait for traffic engine ports ──────────────────────────────────
info "Step 4: Waiting for traffic engines to open their listen ports..."

wait_for_port() {
    local port="$1"
    local label="$2"
    local waited=0
    local max=60
    until nc -z localhost "${port}" 2>/dev/null; do
        if [[ ${waited} -ge ${max} ]]; then
            die "${label} port ${port} did not open within ${max}s"
        fi
        sleep 1
        waited=$((waited + 1))
    done
    info "  ${label} ready on port ${port}"
}

wait_for_port "${TE_A_PORT}" "ixia-c-te-a"
wait_for_port "${TE_B_PORT}" "ixia-c-te-b"

# ─── Step 5: Inject location_map into controller ────────────────────────────
info "Step 5: Injecting location_map config into controller..."

TMPCONFIG="$(mktemp /tmp/ixia-c-config.XXXXXX.yaml)"
cat > "${TMPCONFIG}" <<EOF
location_map:
  - location: ${VETH_A}
    endpoint: localhost:${TE_A_PORT}
  - location: ${VETH_Z}
    endpoint: localhost:${TE_B_PORT}
EOF

docker exec keng-controller mkdir -p "$(dirname "${CONTROLLER_CONFIG_PATH}")"
docker cp "${TMPCONFIG}" "keng-controller:${CONTROLLER_CONFIG_PATH}"
# Fix file permissions — docker cp creates as root mode 600; controller runs as non-root
sudo docker exec -u root keng-controller chmod 644 "${CONTROLLER_CONFIG_PATH}"
rm -f "${TMPCONFIG}"
info "  location_map injected and permissions fixed"

# ─── Step 6: Validate controller responds ───────────────────────────────────
info "Step 6: Validating controller API..."
HTTP_RESPONSE=$(curl -sk -o /dev/null -w "%{http_code}" "${CONTROLLER_URL}/config")
if [[ "${HTTP_RESPONSE}" == "200" ]]; then
    info "  Controller responding at ${CONTROLLER_URL}/config (HTTP ${HTTP_RESPONSE})"
else
    warn "  Unexpected HTTP response: ${HTTP_RESPONSE} — controller may still be initializing"
    info "  Manual check: curl -k ${CONTROLLER_URL}/config"
fi

# ─── Step 7: Print summary ───────────────────────────────────────────────────
echo ""
echo "================================================================"
echo " Ixia-c B2B Deployment Ready"
echo "================================================================"
echo " Controller:    ${CONTROLLER_URL}"
echo " Traffic Engine A:  localhost:${TE_A_PORT}  (interface: ${VETH_A})"
echo " Traffic Engine B:  localhost:${TE_B_PORT}  (interface: ${VETH_Z})"
echo ""
echo " OTG Port Locations:"
echo "   te_a -> \"${VETH_A}\""
echo "   te_b -> \"${VETH_Z}\""
echo ""
echo " Teardown:"
echo "   sudo ./setup-ixia-c-b2b.sh --teardown"
echo "================================================================"
