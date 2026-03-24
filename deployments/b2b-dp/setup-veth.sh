#!/usr/bin/env bash
# setup-veth.sh — Idempotent veth pair + location_map injection for B2B DP deployment
#
# Run this script AFTER docker compose up -d, or before if using --net=host
# (for --net=host the veth pair must exist before the traffic engine starts
#  so it can bind to the interface immediately).
#
# This script is idempotent: safe to run multiple times.

set -euo pipefail

CONTROLLER_CONTAINER="b2b-dp-keng-controller-1"
CONFIG_PATH="/home/ixia-c/controller/config/config.yaml"

# ── 1. Create veth pair (idempotent) ──────────────────────────────────────────
echo "[setup] Checking veth pair..."
if ! ip link show veth-a &>/dev/null; then
    echo "[setup] Creating veth pair veth-a <-> veth-z"
    sudo ip link add veth-a type veth peer name veth-z
else
    echo "[setup] veth-a already exists, skipping creation"
fi

sudo ip link set veth-a up
sudo ip link set veth-z up
echo "[setup] veth-a and veth-z are up"

# ── 2. Wait for traffic engine ports to be ready ──────────────────────────────
echo "[setup] Waiting for traffic engine on port 5555..."
timeout 30 bash -c 'until nc -z localhost 5555 2>/dev/null; do sleep 0.5; done'
echo "[setup] TE port 5555 ready"

echo "[setup] Waiting for traffic engine on port 5556..."
timeout 30 bash -c 'until nc -z localhost 5556 2>/dev/null; do sleep 0.5; done'
echo "[setup] TE port 5556 ready"

# ── 3. Inject location_map into controller ────────────────────────────────────
echo "[setup] Injecting location_map into controller..."

TMPFILE=$(mktemp /tmp/ixia-c-config-XXXXXX.yaml)
cat > "${TMPFILE}" << 'EOF'
location_map:
  - location: veth-a
    endpoint: localhost:5555
  - location: veth-z
    endpoint: localhost:5556
EOF

# Ensure config directory exists inside container
docker exec "${CONTROLLER_CONTAINER}" mkdir -p /home/ixia-c/controller/config

# Copy config file
docker cp "${TMPFILE}" "${CONTROLLER_CONTAINER}:${CONFIG_PATH}"

# Fix permissions (docker cp creates file as root:root mode 600; controller needs to read it)
docker exec -u root "${CONTROLLER_CONTAINER}" chmod 644 "${CONFIG_PATH}"

rm -f "${TMPFILE}"

echo "[setup] location_map injected"

# ── 4. Verify controller responds ─────────────────────────────────────────────
echo "[setup] Verifying controller at https://localhost:8443..."
sleep 1
RESPONSE=$(curl -sk https://localhost:8443/config)
echo "[setup] Controller /config response: ${RESPONSE}"

if [ "${RESPONSE}" = "{}" ] || echo "${RESPONSE}" | grep -q "location_map"; then
    echo "[setup] Controller is healthy"
else
    echo "[ERROR] Unexpected controller response. Check container logs:"
    echo "  docker logs ${CONTROLLER_CONTAINER}"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Ixia-c B2B DP deployment ready"
echo "=========================================="
echo "  Controller:  https://localhost:8443"
echo "  Port te1:    location=veth-a  (TE port 5555)"
echo "  Port te2:    location=veth-z  (TE port 5556)"
echo "=========================================="
