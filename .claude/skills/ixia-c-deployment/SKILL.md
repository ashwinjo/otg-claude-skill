---
name: ixia-c-deployment
description: |
  Deploy and configure Ixia-c containerized traffic generator for OTG testing.
  Use this skill whenever you need to set up Ixia-c infrastructure before running tests.
  Covers Docker Compose (simple labs) and Containerlab (network topology labs).
  Include ixia-c-one, controller, traffic-engine, and protocol-engine setup.
---

# Ixia-c Deployment Guide

Deploy containerized Ixia-c traffic generator for OTG (Open Traffic Generator) testing.

---

## What is Ixia-c?

Ixia-c is a modern, API-driven, containerized traffic generator designed for network testing, emulation, and validation.

**Key characteristics:**
- **OTG-compliant** — Implements Open Traffic Generator API (vendor-neutral)
- **Multi-container** — Controller + Traffic Engine + optional Protocol Engine
- **Free for basic use** — Open-source or commercial licensing available
- **Container-native** — Deploys on Docker, Kubernetes, Containerlab

**Two packaging options:**
1. **Full Ixia-c** — Multiple containers for controller, traffic engines, protocol engines (scaling flexibility)
2. **ixia-c-one** — Single-container package optimized for Containerlab (simpler topologies)

---

## Prerequisites

**System Requirements:**
- **CPU:** At least 2 x86_64 cores
- **RAM:** 7 GB minimum
- **OS:** Ubuntu 22.04 LTS (recommended)
- **Docker:** Docker Engine (Community Edition) 20.10+
- **Python:** Python 3.8+ (for snappi client)

**Port Requirements:**
- **8443/HTTPS** — Controller API (for snappi and OTG clients)
- **50000-50100** — Traffic engine ports (internal, if using multi-container)

**Network:**
- Each Ixia-c instance needs its own unique container hostname/IP
- For multi-container: controllers and engines communicate via internal Docker network

---

## Method 1: Docker Compose (Primary)

**Best for:** Single-lab testing, simple topologies, development

### 1.1 Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  controller:
    image: ghcr.io/open-traffic-generator/ixia-c-controller:0.0.1-2914
    container_name: ixia-c-controller
    entrypoint: controller
    ports:
      - "8443:8443"
    environment:
      - ENABLE_GRPC=0
    networks:
      - ixia-c-net
    healthcheck:
      test: ["CMD", "curl", "-kL", "https://localhost:8443/api/v1/config"]
      interval: 10s
      timeout: 5s
      retries: 3

  traffic-engine-1:
    image: ghcr.io/open-traffic-generator/ixia-c-traffic-engine:0.0.1-2914
    container_name: ixia-c-traffic-engine-1
    entrypoint: traffic-engine
    environment:
      - CONTROLLER=controller:50000
      - LISTEN_PORT=5555
    depends_on:
      controller:
        condition: service_healthy
    networks:
      - ixia-c-net
    privileged: true  # Required for packet manipulation

  traffic-engine-2:
    image: ghcr.io/open-traffic-generator/ixia-c-traffic-engine:0.0.1-2914
    container_name: ixia-c-traffic-engine-2
    entrypoint: traffic-engine
    environment:
      - CONTROLLER=controller:50000
      - LISTEN_PORT=5556
    depends_on:
      controller:
        condition: service_healthy
    networks:
      - ixia-c-net
    privileged: true

networks:
  ixia-c-net:
    driver: bridge
```

**Image Tags:**
- Replace `0.0.1-2914` with the latest version from [GitHub Releases](https://github.com/open-traffic-generator/ixia-c/releases)
- Check `ghcr.io/open-traffic-generator/ixia-c-*` for available versions

### 1.2 Deploy Ixia-c

```bash
# Start all services
docker compose up -d

# Wait for controller to be ready
sleep 10

# Verify deployment
docker compose logs -f controller

# Check health
curl -kL https://localhost:8443/api/v1/config
# Should return empty config: {"ports": []}
```

### 1.3 Verify Containers are Running

```bash
docker compose ps
# Expected output:
# NAME                          STATUS
# ixia-c-controller             Up (healthy)
# ixia-c-traffic-engine-1       Up
# ixia-c-traffic-engine-2       Up
```

### 1.4 Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes (to reset state)
docker compose down -v

# Remove images (to free disk space)
docker rmi \
  ghcr.io/open-traffic-generator/ixia-c-controller:0.0.1-2914 \
  ghcr.io/open-traffic-generator/ixia-c-traffic-engine:0.0.1-2914
```

---

## Method 2: Containerlab (Topology Labs)

**Best for:** Network emulation labs with DUT (Device Under Test), complex topologies

### 2.1 Create `topology.clab.yml`

```yaml
name: ixia-c-lab
topology:
  nodes:
    # DUT (Device Under Test) - e.g., Cisco IOS-XR
    dut:
      kind: ceos
      image: ceos:4.27.0F
      mgmt_ipv4: 172.20.20.2

    # Ixia-c traffic generator (single container)
    ixia-c:
      kind: ixia-c-one
      mgmt_ipv4: 172.20.20.10
      env:
        IXIA_API_KEY: "ixia-api"  # Optional API key
      ports:
        # Port 1: Connected to DUT Ethernet0/0/0/0
        - name: eth1
          status: "up"
        # Port 2: Connected to DUT Ethernet0/0/0/1 (or loopback for bidirectional)
        - name: eth2
          status: "up"

  links:
    # Ixia Port 1 → DUT Interface 1
    - endpoints: ["ixia-c:eth1", "dut:eth1"]
    # Ixia Port 2 → DUT Interface 2
    - endpoints: ["ixia-c:eth2", "dut:eth2"]

  mgmt:
    network: mgmt
    ipv4_subnet: 172.20.20.0/24
```

### 2.2 Deploy Containerlab Topology

```bash
# Deploy topology
sudo containerlab deploy -t topology.clab.yml

# Expected output:
# Name                    Status     Address
# ixia-c                  RUNNING    172.20.20.10
# dut                     RUNNING    172.20.20.2

# View topology
sudo containerlab graph -t topology.clab.yml

# Verify Ixia-c is reachable
curl -kL https://172.20.20.10:8443/api/v1/config
```

### 2.3 Destroy Topology

```bash
# Cleanup
sudo containerlab destroy -t topology.clab.yml

# Remove all images
sudo docker rmi ghcr.io/open-traffic-generator/ixia-c-one:*
```

---

## Method 3: Ixia-c Operator (K8s/KNE)

**Best for:** Kubernetes deployments, cloud-native labs

For Kubernetes Network Emulation (KNE) or Kubernetes deployments, use the [Ixia-c Operator](https://github.com/open-traffic-generator/ixia-c-operator).

**Quick reference:**
```bash
# Install operator
kubectl apply -f https://github.com/open-traffic-generator/ixia-c-operator/releases/...

# Create Ixia-c instance
kubectl apply -f ixia-c-deployment.yaml
```

See [GitHub documentation](https://github.com/open-traffic-generator/ixia-c-operator) for full setup.

---

## Method 4: OpenConfig KNE

**Best for:** Multi-vendor topology labs with Kubernetes

[OpenConfig KNE](https://github.com/openconfig/kne) enables rapid Kubernetes-based network emulation labs with Ixia-c, Cisco, Arista, and other vendors.

Reference: [KNE Deployment Guide](https://github.com/openconfig/kne/tree/main/docs)

---

## Post-Deployment Verification

### Verify Controller API

```bash
# Check controller health
curl -kL https://localhost:8443/api/v1/config

# Expected response (empty config):
# {"ports": []}
```

### Python Snappi Connection Test

Save as `verify_ixia_c.py`:

```python
#!/usr/bin/env python3
"""
Minimal Snappi connection test to verify Ixia-c deployment
"""

import snappi
import sys
import json

CONTROLLER_IP = "localhost"
CONTROLLER_PORT = 8443

def test_connection():
    """Test Snappi API connection to Ixia-c controller"""

    location = f"https://{CONTROLLER_IP}:{CONTROLLER_PORT}"

    try:
        print(f"[1] Connecting to controller at {location}...")
        api = snappi.api(location=location, verify=False)
        print("    ✓ Connection successful")

        print(f"\n[2] Testing config get/set...")
        # Get current config (empty)
        config = api.get_config()
        print(f"    ✓ Current config: {len(config.ports)} ports, {len(config.devices)} devices")

        # Create minimal config
        config = api.config()
        config.ports.port(name='p1')
        api.set_config(config)
        print("    ✓ Config loaded: 1 port")

        print(f"\n[3] Testing metrics request...")
        req = snappi.MetricsRequest()
        req.choice = req.PORT
        resp = api.get_metrics(req)
        print(f"    ✓ Metrics returned: {len(resp.port_metrics)} port metrics")

        print("\n✅ Ixia-c deployment verified successfully")
        return True

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        print("\nTroubleshooting:")
        print("  - Check if Docker containers are running: docker ps")
        print("  - Check controller logs: docker logs ixia-c-controller")
        print("  - Check network connectivity: ping localhost 8443")
        print("  - Verify snappi is installed: pip install snappi")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
```

**Run verification:**
```bash
pip install snappi
python verify_ixia_c.py
# Expected:
# [1] Connecting to controller at https://localhost:8443...
#     ✓ Connection successful
# [2] Testing config get/set...
#     ✓ Current config: 1 ports, 0 devices
# [3] Testing metrics request...
#     ✓ Metrics returned: 1 port metrics
# ✅ Ixia-c deployment verified successfully
```

---

## Integration with Snappi

### Infrastructure YAML Template

Once Ixia-c is deployed, create an infrastructure file for the snappi-script-generator skill:

**`infrastructure.yaml`:**
```yaml
controller:
  ip: "localhost"          # or IP where ixia-c is deployed
  port: 8443
  protocol: "https"

ports:
  - name: "P1"
    location: "1/1"        # Ixia-c port identifier
  - name: "P2"
    location: "1/2"

test_config:
  duration_seconds: 60
  metrics_interval_seconds: 5
  stop_on_failure: false
```

### Flow with snappi-script-generator

1. **Deploy Ixia-c** (this skill) → `docker compose up -d`
2. **Generate OTG config** → `/otg-config-generator`
3. **Generate Snappi script** → `/snappi-script-generator` + infrastructure.yaml
4. **Run test** → `python test_bgp.py`

---

## Troubleshooting

### Issue: Controller not starting

**Symptom:** `docker logs ixia-c-controller` shows errors

**Fix:**
```bash
# Check if port 8443 is already in use
lsof -i :8443

# If in use, stop conflicting service or use different port in docker-compose.yml
# ports:
#   - "8444:8443"  # Map to host port 8444
```

### Issue: Traffic engine can't connect to controller

**Symptom:** Traffic engine logs show "cannot connect to controller"

**Fix:**
```bash
# Check Docker network
docker network inspect ixia-c-net

# Verify controller is on same network
docker inspect ixia-c-controller | grep -A 5 NetworkSettings

# Rebuild network
docker compose down
docker compose up -d
```

### Issue: Snappi can't reach controller

**Symptom:** `ConnectionRefusedError` from Python script

**Fix:**
```bash
# Check container is running and healthy
docker compose ps

# Test API directly from host
curl -kL https://localhost:8443/api/v1/config

# If curl works but snappi fails, verify snappi version
pip show snappi
# Ensure >= 0.10.0

# Update if needed
pip install --upgrade snappi
```

### Issue: Port assignment fails

**Symptom:** OTG config rejected, port "not found"

**Fix:**
```bash
# Get actual port names from traffic engines
docker exec ixia-c-traffic-engine-1 traffic-engine --help

# Port names depend on traffic engine; check against your infrastructure.yaml
# May need to adjust port location format (e.g., "1/1" vs "eth1")
```

### Issue: Protocol engine required but missing

**Symptom:** BGP/ISIS config loaded but protocols don't start

**Context:** BGP and ISIS require a separate protocol-engine container. For simple traffic-only tests, skip BGP/ISIS.

**Fix:**
Add protocol-engine service to `docker-compose.yml`:
```yaml
  protocol-engine:
    image: ghcr.io/open-traffic-generator/ixia-c-protocol-engine:0.0.1-2914
    container_name: ixia-c-protocol-engine
    entrypoint: protocol-engine
    environment:
      - CONTROLLER=controller:50000
    depends_on:
      controller:
        condition: service_healthy
    networks:
      - ixia-c-net
```

---

## Performance Tuning

### Containerlab Resource Limits

For high-throughput testing, increase resource allocation:

```yaml
# In topology.clab.yml
nodes:
  ixia-c:
    kind: ixia-c-one
    config:
      resources:
        limits:
          memory: 8Gi
          cpus: '4'
        requests:
          memory: 4Gi
          cpus: '2'
```

### Docker Compose Resource Limits

```yaml
# In docker-compose.yml
services:
  traffic-engine-1:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## Best Practices

1. **Health checks** — Always use `healthcheck` in docker-compose to ensure controller is ready before starting engines
2. **Network isolation** — Use dedicated Docker network for Ixia-c containers
3. **Cleanup** — Always `docker compose down` or `containerlab destroy` when done to free resources
4. **Logging** — Enable DEBUG logs during troubleshooting: `--loglevel DEBUG` in entrypoint
5. **Scaling** — For multiple test engines, deploy multiple traffic-engine services
6. **Version pinning** — Use specific image tags (not `latest`) for reproducibility

---

## Reference

- **GitHub:** https://github.com/open-traffic-generator/ixia-c
- **Examples:** https://github.com/open-traffic-generator/otg-examples
- **API Docs:** https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-traffic-generator/models/main/yaml/otg.yaml
- **Snappi SDK:** https://github.com/open-traffic-generator/snappi

