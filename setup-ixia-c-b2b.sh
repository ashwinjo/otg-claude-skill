#!/bin/bash
set -e

echo "=== Ixia-c B2B Dataplane Deployment Setup ==="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Create veth pair
echo -e "${YELLOW}Step 1: Creating veth pair (veth-a <-> veth-b)${NC}"
if ip link show veth-a &>/dev/null; then
    echo "  ⚠ veth-a already exists, skipping..."
else
    sudo ip link add veth-a type veth peer name veth-b
    sudo ip link set veth-a up
    sudo ip link set veth-b up
    echo -e "  ${GREEN}✓ Created veth-a <-> veth-b${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Starting Docker containers${NC}"
sudo docker compose -f docker-compose-b2b-dataplane.yml up -d
echo -e "  ${GREEN}✓ Started keng-controller, ixia-c-te-a, ixia-c-te-b${NC}"

echo ""
echo -e "${YELLOW}Step 3: Waiting for controller to be ready${NC}"
max_retries=30
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -sk https://localhost:8443/config &>/dev/null; then
        echo -e "  ${GREEN}✓ Controller is ready${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "  Waiting... ($retry_count/$max_retries)"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo -e "  ${RED}✗ Controller not responding after ${max_retries} attempts${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 4: Verifying container health${NC}"
echo "Containers:"
sudo docker ps --filter "name=keng-controller\|ixia-c-te" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo -e "${YELLOW}Step 5: Port mapping and configuration${NC}"
cat > port-mapping.json << 'EOF'
{
  "deployment": "b2b-dataplane",
  "method": "Docker Compose",
  "controller": {
    "name": "keng-controller",
    "url": "https://localhost:8443",
    "ports": ["8443 (HTTPS REST)", "40051 (gRPC)"]
  },
  "traffic_engines": [
    {
      "name": "ixia-c-te-a",
      "listen_port": 5555,
      "veth": "veth-a",
      "location": "veth-a"
    },
    {
      "name": "ixia-c-te-b",
      "listen_port": 5556,
      "veth": "veth-b",
      "location": "veth-b"
    }
  ],
  "veth_pair": {
    "a": "veth-a",
    "b": "veth-b",
    "mtu": 1500
  },
  "controller_location_map": [
    {
      "location": "veth-a",
      "endpoint": "localhost:5555"
    },
    {
      "location": "veth-b",
      "endpoint": "localhost:5556"
    }
  ]
}
EOF
echo -e "  ${GREEN}✓ Saved port mapping to port-mapping.json${NC}"

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Infrastructure ready for OTG config injection:"
echo "  • Controller: https://localhost:8443"
echo "  • Port A (veth-a): localhost:5555"
echo "  • Port B (veth-b): localhost:5556"
echo ""
echo "Next: Generate OTG config and Snappi script"
