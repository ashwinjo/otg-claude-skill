#!/usr/bin/env bash
# setup-ixia-c-bgp.sh — Ixia-c BGP B2B veth setup and controller configuration
#
# Run this AFTER "sudo docker compose -f docker-compose-bgp-cpdp.yml up -d"
#
# What this script does:
#   1. Waits for all containers to reach Running state
#   2. Creates the veth-a <-> veth-z pair on the host (idempotent)
#   3. Pushes veth-a into the ixia-c-traffic-engine-a network namespace
#   4. Pushes veth-z into the ixia-c-traffic-engine-z network namespace
#   5. Discovers TE container IPs
#   6. Waits for traffic engine listen ports to be ready
#   7. Injects location_map config into the controller
#   8. Verifies controller health
#   9. Prints port mapping summary for downstream OTG config generators
#
# Usage:
#   sudo bash setup-ixia-c-bgp.sh
#
# Requirements:
#   - Must be run as root (or with sudo) — ip link / netns operations require it
#   - Docker must be installed and running
#   - nc (netcat) must be available for port readiness checks

set -euo pipefail

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
CONTROLLER_CONTAINER="keng-controller"
TE_A_CONTAINER="ixia-c-traffic-engine-a"
TE_Z_CONTAINER="ixia-c-traffic-engine-z"
VETH_A="veth-a"
VETH_Z="veth-z"
CONTROLLER_PORT="8443"
COMPOSE_FILE="docker-compose-bgp-cpdp.yml"

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
log()  { echo "[setup] $*"; }
err()  { echo "[ERROR] $*" >&2; exit 1; }

# push_ifc_to_container <interface> <container-name>
# Moves a veth interface from the host netns into a container's network namespace.
push_ifc_to_container() {
    local ifc="$1"
    local container="$2"

    log "Pushing ${ifc} into container ${container}..."

    local cid cpid
    cid=$(docker inspect --format="{{json .Id}}" "${container}" | cut -d'"' -f2)
    cpid=$(docker inspect --format="{{json .State.Pid}}" "${container}" | cut -d'"' -f2)

    [ -z "${cid}"  ] && err "Could not get container ID for ${container}"
    [ -z "${cpid}" ] && err "Could not get container PID for ${container}"

    mkdir -p /var/run/netns
    ln -sf /proc/${cpid}/ns/net /var/run/netns/${cid}
    ip link set "${ifc}" netns "${cid}"
    ip netns exec "${cid}" ip link set "${ifc}" name "${ifc}"
    ip netns exec "${cid}" ip -4 addr add 0/0 dev "${ifc}"
    ip netns exec "${cid}" ip -4 link set "${ifc}" up
    rm -rf /var/run/netns/${cid}

    log "${ifc} is now inside ${container}."
}

# ----------------------------------------------------------------------------
# Step 1: Verify containers are running
# ----------------------------------------------------------------------------
log "Waiting for containers to reach Running state..."
for container in "${CONTROLLER_CONTAINER}" "${TE_A_CONTAINER}" "${TE_Z_CONTAINER}"; do
    attempt=0
    until [ "$(docker inspect --format='{{.State.Running}}' "${container}" 2>/dev/null)" = "true" ]; do
        attempt=$((attempt + 1))
        [ "${attempt}" -ge 30 ] && err "Timed out waiting for ${container} to start. Run: docker compose -f ${COMPOSE_FILE} ps"
        log "  Waiting for ${container} (attempt ${attempt}/30)..."
        sleep 2
    done
    log "  ${container} is running."
done

# ----------------------------------------------------------------------------
# Step 2: Create veth pair on host (idempotent)
# ----------------------------------------------------------------------------
log "Creating veth pair ${VETH_A} <-> ${VETH_Z}..."
if ip link show "${VETH_A}" &>/dev/null; then
    log "  ${VETH_A} already exists — skipping creation."
else
    ip link add "${VETH_A}" type veth peer name "${VETH_Z}"
    ip link set "${VETH_A}" up
    ip link set "${VETH_Z}" up
    log "  veth pair created and brought up."
fi

# ----------------------------------------------------------------------------
# Step 3: Push veth interfaces into container namespaces
# ----------------------------------------------------------------------------
push_ifc_to_container "${VETH_A}" "${TE_A_CONTAINER}"
push_ifc_to_container "${VETH_Z}" "${TE_Z_CONTAINER}"

# ----------------------------------------------------------------------------
# Step 4: Discover container IPs
# ----------------------------------------------------------------------------
log "Discovering container IP addresses..."
TE_A_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${TE_A_CONTAINER}")
TE_Z_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${TE_Z_CONTAINER}")

[ -z "${TE_A_IP}" ] && err "Could not get IP for ${TE_A_CONTAINER}. Check: docker inspect ${TE_A_CONTAINER}"
[ -z "${TE_Z_IP}" ] && err "Could not get IP for ${TE_Z_CONTAINER}. Check: docker inspect ${TE_Z_CONTAINER}"

log "  ${TE_A_CONTAINER} IP: ${TE_A_IP}"
log "  ${TE_Z_CONTAINER} IP: ${TE_Z_IP}"

# ----------------------------------------------------------------------------
# Step 5: Wait for traffic engine listen ports to be ready (port 5555 on each TE)
# ----------------------------------------------------------------------------
log "Waiting for traffic engine data ports to be ready..."

attempt=0
until nc -z "${TE_A_IP}" 5555 2>/dev/null; do
    attempt=$((attempt + 1))
    [ "${attempt}" -ge 60 ] && err "Timed out waiting for ${TE_A_CONTAINER}:5555. Check WAIT_FOR_IFACE and veth push."
    log "  Waiting for ${TE_A_CONTAINER}:5555 (attempt ${attempt}/60)..."
    sleep 1
done
log "  ${TE_A_CONTAINER}:5555 is ready."

attempt=0
until nc -z "${TE_Z_IP}" 5555 2>/dev/null; do
    attempt=$((attempt + 1))
    [ "${attempt}" -ge 60 ] && err "Timed out waiting for ${TE_Z_CONTAINER}:5555. Check WAIT_FOR_IFACE and veth push."
    log "  Waiting for ${TE_Z_CONTAINER}:5555 (attempt ${attempt}/60)..."
    sleep 1
done
log "  ${TE_Z_CONTAINER}:5555 is ready."

# ----------------------------------------------------------------------------
# Step 6: Inject location_map into controller
# The controller needs this to map OTG port location names to TE endpoints.
# Format: "<te-ip>:5555+<te-ip>:50071"  (TE data port + PE gRPC port, same netns)
# ----------------------------------------------------------------------------
log "Injecting location_map into controller..."

TMPCONFIG=$(mktemp /tmp/keng-config-XXXXXX.yaml)
cat > "${TMPCONFIG}" << EOF
location_map:
  - location: veth-a
    endpoint: "${TE_A_IP}:5555+${TE_A_IP}:50071"
  - location: veth-z
    endpoint: "${TE_Z_IP}:5555+${TE_Z_IP}:50071"
EOF

docker exec "${CONTROLLER_CONTAINER}" mkdir -p /home/ixia-c/controller/config
docker cp "${TMPCONFIG}" "${CONTROLLER_CONTAINER}":/home/ixia-c/controller/config/config.yaml
rm -f "${TMPCONFIG}"

log "  location_map injected."

# ----------------------------------------------------------------------------
# Step 7: Verify controller health
# Allow a brief settling period after config injection.
# ----------------------------------------------------------------------------
log "Verifying controller at https://localhost:${CONTROLLER_PORT}/config ..."
sleep 3

RESP=$(curl -sk "https://localhost:${CONTROLLER_PORT}/config" 2>&1 || true)
if echo "${RESP}" | grep -q "{}"; then
    log "  Controller is healthy — returned empty config ({})."
else
    log "  Controller response: ${RESP}"
    log "  (Non-empty response may indicate config is loaded — this can be normal.)"
fi

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo "================================================================"
echo " Ixia-c BGP B2B Deployment Ready"
echo "================================================================"
echo " Compose file:  ${COMPOSE_FILE}"
echo " Controller:    https://localhost:${CONTROLLER_PORT}"
echo ""
echo " Port mapping:"
printf "   te1  location=veth-a  ->  %s:5555+%s:50071\n" "${TE_A_IP}" "${TE_A_IP}"
printf "   te2  location=veth-z  ->  %s:5555+%s:50071\n" "${TE_Z_IP}" "${TE_Z_IP}"
echo ""
echo " OTG port locations (use these in your OTG config / Snappi script):"
echo "   Port 1:  location = \"veth-a\""
echo "   Port 2:  location = \"veth-z\""
echo ""
echo " Port mapping JSON (for otg-config-generator-agent):"
printf ' {"te1": "veth-a", "te2": "veth-z"}\n'
echo ""
echo " Cleanup:"
echo "   sudo docker compose -f ${COMPOSE_FILE} down && sudo ip link delete veth-a"
echo "================================================================"
