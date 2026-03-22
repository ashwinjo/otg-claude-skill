#!/usr/bin/env bash
# setup-veth.sh — BGP B2B veth setup and controller location_map injection
#
# Run this AFTER "sudo docker compose up -d" has started all containers.
# This script:
#   1. Creates the veth-a <-> veth-z pair on the host
#   2. Pushes veth-a into the ixia-c-traffic-engine-a namespace
#   3. Pushes veth-z into the ixia-c-traffic-engine-z namespace
#   4. Discovers container IPs
#   5. Injects the location_map config into the controller
#
# Usage: sudo bash setup-veth.sh

set -euo pipefail

CONTROLLER_CONTAINER="keng-controller"
TE_A_CONTAINER="ixia-c-traffic-engine-a"
TE_Z_CONTAINER="ixia-c-traffic-engine-z"
VETH_A="veth-a"
VETH_Z="veth-z"
CONTROLLER_PORT="8443"

# ----------------------------------------------------------------------------
# Helper: push a veth interface into a container's network namespace
# ----------------------------------------------------------------------------
push_ifc_to_container() {
    local ifc="$1"
    local container="$2"

    echo "[setup] Pushing ${ifc} into container ${container}..."

    local cid cpid
    cid=$(docker inspect --format="{{json .Id}}" "${container}" | cut -d'"' -f2)
    cpid=$(docker inspect --format="{{json .State.Pid}}" "${container}" | cut -d'"' -f2)

    sudo mkdir -p /var/run/netns
    sudo ln -sf /proc/${cpid}/ns/net /var/run/netns/${cid}
    sudo ip link set "${ifc}" netns "${cid}"
    sudo ip netns exec "${cid}" ip link set "${ifc}" name "${ifc}"
    sudo ip netns exec "${cid}" ip -4 addr add 0/0 dev "${ifc}"
    sudo ip netns exec "${cid}" ip -4 link set "${ifc}" up
    sudo rm -rf /var/run/netns/${cid}

    echo "[setup] ${ifc} is now inside ${container}."
}

# ----------------------------------------------------------------------------
# Step 1: Wait for containers to be running
# ----------------------------------------------------------------------------
echo "[setup] Waiting for containers to be running..."
for container in "${CONTROLLER_CONTAINER}" "${TE_A_CONTAINER}" "${TE_Z_CONTAINER}"; do
    until [ "$(docker inspect --format='{{.State.Running}}' "${container}" 2>/dev/null)" = "true" ]; do
        echo "[setup]   Waiting for ${container}..."
        sleep 2
    done
    echo "[setup]   ${container} is running."
done

# ----------------------------------------------------------------------------
# Step 2: Create veth pair on host (idempotent)
# ----------------------------------------------------------------------------
echo "[setup] Creating veth pair ${VETH_A} <-> ${VETH_Z}..."
if ip link show "${VETH_A}" &>/dev/null; then
    echo "[setup]   ${VETH_A} already exists — skipping creation."
else
    sudo ip link add "${VETH_A}" type veth peer name "${VETH_Z}"
    sudo ip link set "${VETH_A}" up
    sudo ip link set "${VETH_Z}" up
    echo "[setup]   veth pair created and brought up."
fi

# ----------------------------------------------------------------------------
# Step 3: Push veth interfaces into container namespaces
# ----------------------------------------------------------------------------
push_ifc_to_container "${VETH_A}" "${TE_A_CONTAINER}"
push_ifc_to_container "${VETH_Z}" "${TE_Z_CONTAINER}"

# ----------------------------------------------------------------------------
# Step 4: Discover container IPs
# ----------------------------------------------------------------------------
echo "[setup] Discovering container IP addresses..."
TE_A_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${TE_A_CONTAINER}")
TE_Z_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${TE_Z_CONTAINER}")

if [ -z "${TE_A_IP}" ] || [ -z "${TE_Z_IP}" ]; then
    echo "[ERROR] Could not determine container IPs."
    docker inspect --format='{{.Name}}: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
        "${TE_A_CONTAINER}" "${TE_Z_CONTAINER}"
    exit 1
fi

echo "[setup]   ${TE_A_CONTAINER} IP: ${TE_A_IP}"
echo "[setup]   ${TE_Z_CONTAINER} IP: ${TE_Z_IP}"

# ----------------------------------------------------------------------------
# Step 5: Wait for traffic engine listen ports to be ready
# ----------------------------------------------------------------------------
echo "[setup] Waiting for traffic engine ports to be ready..."
until nc -z "${TE_A_IP}" 5555 2>/dev/null; do
    echo "[setup]   Waiting for ${TE_A_CONTAINER}:5555..."
    sleep 1
done
echo "[setup]   ${TE_A_CONTAINER}:5555 is ready."

until nc -z "${TE_Z_IP}" 5555 2>/dev/null; do
    echo "[setup]   Waiting for ${TE_Z_CONTAINER}:5555..."
    sleep 1
done
echo "[setup]   ${TE_Z_CONTAINER}:5555 is ready."

# ----------------------------------------------------------------------------
# Step 6: Inject location_map into controller
# ----------------------------------------------------------------------------
echo "[setup] Injecting location_map into controller..."

cat > /tmp/keng-config.yaml << EOF
location_map:
  - location: veth-a
    endpoint: "${TE_A_IP}:5555+${TE_A_IP}:50071"
  - location: veth-z
    endpoint: "${TE_Z_IP}:5555+${TE_Z_IP}:50071"
EOF

docker exec "${CONTROLLER_CONTAINER}" mkdir -p /home/ixia-c/controller/config
docker cp /tmp/keng-config.yaml "${CONTROLLER_CONTAINER}":/home/ixia-c/controller/config/config.yaml
rm -f /tmp/keng-config.yaml

echo "[setup]   location_map injected."

# ----------------------------------------------------------------------------
# Step 7: Verify controller is reachable
# ----------------------------------------------------------------------------
echo "[setup] Verifying controller at https://localhost:${CONTROLLER_PORT}/config ..."
sleep 3
if curl -sk "https://localhost:${CONTROLLER_PORT}/config" | grep -q "{}"; then
    echo "[setup]   Controller is healthy and returning empty config."
else
    RESP=$(curl -sk "https://localhost:${CONTROLLER_PORT}/config")
    echo "[setup]   Controller response: ${RESP}"
fi

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo "================================================================"
echo " Ixia-c BGP B2B Deployment Ready"
echo "================================================================"
echo " Controller:  https://localhost:${CONTROLLER_PORT}"
echo " Port mapping:"
echo "   te1 (veth-a) -> ${TE_A_IP}:5555 + ${TE_A_IP}:50071"
echo "   te2 (veth-z) -> ${TE_Z_IP}:5555 + ${TE_Z_IP}:50071"
echo ""
echo " OTG port locations for config generator:"
echo "   Port 1: location = veth-a"
echo "   Port 2: location = veth-z"
echo "================================================================"
echo ""
echo "Cleanup command:"
echo "  sudo docker compose down && sudo ip link delete veth-a"
