#!/usr/bin/env bash
# teardown.sh — Full cleanup for B2B DP Ixia-c deployment
#
# Stops containers, removes volumes, and deletes veth pair.
# Safe to run even if deployment is partially up.

set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[teardown] Stopping Docker Compose stack..."
docker compose -f "${DEPLOY_DIR}/docker-compose.yml" down --volumes 2>/dev/null || true

echo "[teardown] Removing veth pair..."
if ip link show veth-a &>/dev/null; then
    sudo ip link delete veth-a
    echo "[teardown] veth-a (and peer veth-z) removed"
else
    echo "[teardown] veth-a not found, skipping"
fi

echo "[teardown] Cleanup complete"
