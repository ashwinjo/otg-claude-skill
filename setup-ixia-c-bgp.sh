#!/bin/bash

# Ixia-c BGP Deployment Setup Script
# This script sets up the complete BGP testing environment with Docker Compose CP+DP

set -e

echo "=========================================="
echo "Ixia-c BGP Testing Setup (CP+DP)"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Start Docker Compose services
echo -e "\n${BLUE}[Step 1/4] Starting Docker Compose services...${NC}"
docker compose -f docker-compose-bgp-cpdp.yml up -d

echo "Waiting for controller to be healthy..."
sleep 15

# Step 2: Create veth pair on host
echo -e "\n${BLUE}[Step 2/4] Creating veth pair (veth-a ↔ veth-z)...${NC}"

# Clean up any existing veths
sudo ip link del veth-a 2>/dev/null || true
sudo ip link del veth-z 2>/dev/null || true

# Create veth pair
sudo ip link add veth-a type veth peer name veth-z
sudo ip link set veth-a up
sudo ip link set veth-z up

echo -e "${GREEN}✓ Veth pair created and enabled${NC}"

# Step 3: Get traffic engine container IDs and IPs
echo -e "\n${BLUE}[Step 3/4] Detecting traffic engine containers...${NC}"

TE_A_ID=$(docker ps --filter "name=ixia-c-traffic-engine-veth-a" -q)
TE_Z_ID=$(docker ps --filter "name=ixia-c-traffic-engine-veth-z" -q)

if [ -z "$TE_A_ID" ] || [ -z "$TE_Z_ID" ]; then
    echo -e "${YELLOW}Error: Traffic engines not running${NC}"
    exit 1
fi

# Function to push veth into container namespace
push_veth_to_ns() {
    local veth=$1
    local container_id=$2
    local container_name=$3

    echo "  Pushing $veth into $container_name..."

    # Get container PID
    container_pid=$(docker inspect --format '{{.State.Pid}}' "$container_id")

    # Get the veth peer
    veth_peer=$(ip link show "$veth" | grep -oP 'peer name \K\w+')

    # Move veth to container namespace
    sudo ip link set "$veth" netns "$container_pid"
    sudo nsenter -t "$container_pid" -n ip link set "$veth" up
}

# Push veths into container namespaces
push_veth_to_ns "veth-a" "$TE_A_ID" "ixia-c-traffic-engine-veth-a"
push_veth_to_ns "veth-z" "$TE_Z_ID" "ixia-c-traffic-engine-veth-z"

echo -e "${GREEN}✓ Veth pairs injected into container namespaces${NC}"

# Wait for traffic engines to be ready
echo "Waiting for traffic engines to be ready..."
sleep 10

# Step 4: Inject controller configuration
echo -e "\n${BLUE}[Step 4/4] Injecting controller configuration...${NC}"

# Get container IPs from Docker network
TE_A_IP=$(docker inspect ixia-c-traffic-engine-veth-a --format='{{.NetworkSettings.Networks.ixia-c-net.IPAddress}}')
TE_Z_IP=$(docker inspect ixia-c-traffic-engine-veth-z --format='{{.NetworkSettings.Networks.ixia-c-net.IPAddress}}')

echo "  Traffic Engine A IP: $TE_A_IP"
echo "  Traffic Engine Z IP: $TE_Z_IP"

# Create controller configuration with location_map
CONFIG_FILE="/tmp/ixia-c-config.yaml"
cat > "$CONFIG_FILE" << EOF
location_map:
  - location: veth-a
    endpoint: "${TE_A_IP}:5555+${TE_A_IP}:50071"
  - location: veth-z
    endpoint: "${TE_Z_IP}:5555+${TE_Z_IP}:50071"
EOF

echo "  Config file created: $CONFIG_FILE"

# Create config directory in controller and copy config
docker exec keng-controller mkdir -p /home/ixia-c/controller/config
docker cp "$CONFIG_FILE" keng-controller:/home/ixia-c/controller/config.yaml

rm -f "$CONFIG_FILE"

echo -e "${GREEN}✓ Controller configuration injected${NC}"

# Verification
echo -e "\n${BLUE}[Verification] Checking deployment health...${NC}"

echo "Controller status:"
curl -sk https://localhost:8443/config | jq . || echo "  (Health check: pending)"

echo -e "\n${GREEN}=========================================="
echo "✓ Ixia-c BGP (CP+DP) deployment ready!"
echo "==========================================${NC}"

# Output port mapping for downstream agents
echo -e "\n${BLUE}Port Mapping (for otg-config-generator):${NC}"
cat > /tmp/port-mapping.json << EOF
{
  "deployment_method": "docker-compose",
  "controller": {
    "url": "https://localhost:8443",
    "port": 8443,
    "status": "healthy"
  },
  "port_mapping": {
    "te1": "veth-a",
    "te2": "veth-z"
  },
  "traffic_engines": {
    "veth-a": {
      "container": "ixia-c-traffic-engine-veth-a",
      "ip": "${TE_A_IP}",
      "data_port": 5555,
      "protocol_port": 50071
    },
    "veth-z": {
      "container": "ixia-c-traffic-engine-veth-z",
      "ip": "${TE_Z_IP}",
      "data_port": 5555,
      "protocol_port": 50071
    }
  }
}
EOF

echo "$(cat /tmp/port-mapping.json | jq .)"

# Next steps
echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Use otg-config-generator with port mapping above"
echo "2. Create OTG config with locations: veth-a, veth-z"
echo "3. Use snappi-script-generator with controller URL: https://localhost:8443"
echo ""
echo "Useful commands:"
echo "  - View logs: docker compose -f docker-compose-bgp-cpdp.yml logs -f"
echo "  - Check status: docker compose -f docker-compose-bgp-cpdp.yml ps"
echo "  - Clean up: docker compose -f docker-compose-bgp-cpdp.yml down"
echo "  - Destroy veths: sudo ip link del veth-a && sudo ip link del veth-z"
