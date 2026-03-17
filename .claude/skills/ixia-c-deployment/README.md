# Ixia-c Deployment Skill

**Deploy and configure Ixia-c containerized traffic generator for OTG testing.**

A Claude AI skill that sets up Ixia-c infrastructure using Docker Compose, Containerlab, or Kubernetes, with verification and troubleshooting guidance.

---

## Table of Contents

- [Quick Start](#quick-start)
- [What This Skill Does](#what-this-skill-does)
- [Deployment Methods](#deployment-methods)
- [System Requirements](#system-requirements)
- [How to Use](#how-to-use)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

---

## Quick Start

### For Claude Code Users (Docker Compose)

```bash
# Invoke the skill in Claude Code:
/ixia-c-deployment
```

Then request a deployment:

```
Prompt: "Deploy Ixia-c with Docker Compose for a simple lab test"
```

**Output:**
```
✅ DEPLOYMENT GUIDE READY

docker-compose.yml    → Multi-container setup (controller + engines)
deployment-steps.md   → Step-by-step instructions

Deploy:
  docker compose up -d

Verify:
  curl -kL https://localhost:8443/api/v1/config
```

### For Claude Code Users (Containerlab)

```
Prompt: "Deploy Ixia-c with Containerlab topology"
```

**Output:**
```
✅ DEPLOYMENT GUIDE READY

topology.clab.yml     → Containerlab topology definition
deployment-steps.md   → Step-by-step instructions

Deploy:
  sudo clab deploy -t topology.clab.yml

Verify:
  curl -kL https://<ixia-c-ip>:8443/api/v1/config
```

---

## What This Skill Does

Provides **configuration and deployment guidance** for Ixia-c traffic generator:

- ✅ Generates Docker Compose files (multi-container setup)
- ✅ Generates Containerlab topologies (network labs)
- ✅ Generates health checks and verification scripts
- ✅ Provides Kubernetes/KNE references
- ✅ Includes troubleshooting guides
- ✅ Performance tuning recommendations
- ✅ Integration guidance with snappi-script-generator

**Key Feature:** Ixia-c is **OTG-compliant, vendor-neutral**, and **free for basic use**.

---

## Deployment Methods

### Method 1: Docker Compose (Recommended for Simple Labs)

**Best for:**
- Single traffic generator instance
- Development and testing
- Quick prototyping

**What it deploys:**
- Controller (API server on port 8443)
- Traffic Engine #1 (packet transmission/reception)
- Traffic Engine #2 (optional, for dual-engine testing)
- Protocol Engine (optional, for BGP/ISIS)

**Example:**
```bash
docker compose up -d
# Ixia-c available at https://localhost:8443
```

### Method 2: Containerlab (Recommended for Network Topologies)

**Best for:**
- Multi-vendor labs (Cisco, Arista, Juniper, etc.)
- Complex network topologies
- Device Under Test (DUT) integration
- Network emulation studies

**What it deploys:**
- ixia-c-one (single-container, production-grade)
- DUT containers (Cisco IOS-XR, cEOS, etc.)
- Interconnected topology

**Example:**
```bash
sudo clab deploy -t topology.clab.yml
# Ixia-c available at 172.20.20.10:8443 (from yaml)
```

### Method 3: Ixia-c Operator (Kubernetes)

**Best for:**
- Cloud-native deployments
- Kubernetes/KNE environments
- Hybrid multi-cloud labs

**Reference:** [Ixia-c Operator GitHub](https://github.com/open-traffic-generator/ixia-c-operator)

### Method 4: OpenConfig KNE

**Best for:**
- Multi-vendor Kubernetes labs
- Google-developed Kubernetes Network Emulation

**Reference:** [KNE GitHub](https://github.com/openconfig/kne)

---

## System Requirements

### Hardware
- **CPU:** At least 2 x86_64 cores
- **RAM:** 7 GB minimum (4GB per traffic engine recommended)
- **Disk:** 5GB free (for container images)

### Software
- **OS:** Ubuntu 22.04 LTS (recommended)
- **Docker:** Community Edition 20.10+ (for Docker Compose)
- **Containerlab:** 0.40+ (for Containerlab method)
- **Python:** 3.8+ with snappi SDK (`pip install snappi`)

### Network
- **Port 8443/HTTPS:** For Ixia-c controller API
- **Ports 50000-50100:** For internal controller-engine communication (Docker only)
- **Separate networks:** For multi-instance deployments

---

## How to Use

### Step 1: Request Deployment Configuration

Invoke the skill:

```bash
/ixia-c-deployment
```

Specify your deployment method:

```
Prompt: "Generate Docker Compose deployment for Ixia-c with controller and 2 traffic engines"
```

Or:

```
Prompt: "Generate Containerlab topology with Ixia-c and a Cisco IOS-XR DUT"
```

### Step 2: Deploy Infrastructure

#### Docker Compose:
```bash
docker compose up -d

# Wait for controller to be healthy
sleep 10

# Check status
docker compose ps
docker compose logs controller
```

#### Containerlab:
```bash
sudo clab deploy -t topology.clab.yml

# Check status
sudo clab inspect -t topology.clab.yml
```

### Step 3: Verify Deployment

Run the Python verification script:

```bash
pip install snappi

python verify_ixia_c.py
# Expected output:
# [1] Connecting to controller...
#     ✓ Connection successful
# [2] Testing config get/set...
#     ✓ Current config: 1 ports, 0 devices
# [3] Testing metrics request...
#     ✓ Metrics returned: 1 port metrics
# ✅ Ixia-c deployment verified successfully
```

### Step 4: Create Infrastructure YAML for snappi-script-generator

Create `infrastructure.yaml` to use with the next skill:

```yaml
controller:
  ip: "localhost"          # or 172.20.20.10 for Containerlab
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

### Step 5: Generate and Run Test Script

Use the next skill to generate tests:

```bash
/snappi-script-generator

# Then run:
pip install snappi
python test_bgp.py
```

---

## Verification

### Method 1: cURL (Quick Check)

```bash
# Docker Compose (localhost)
curl -kL https://localhost:8443/api/v1/config

# Containerlab (from yaml IP)
curl -kL https://172.20.20.10:8443/api/v1/config

# Expected response:
# {"ports": []}
```

### Method 2: Python snappi (Comprehensive)

Script provided in SKILL.md:

```bash
python verify_ixia_c.py
```

Tests:
- API connectivity
- Configuration load/save
- Metrics collection

### Method 3: Docker Health Checks

```bash
# Docker Compose
docker compose ps

# Should show:
# NAME                       STATUS
# ixia-c-controller          Up (healthy)
# ixia-c-traffic-engine-1    Up
```

---

## Troubleshooting

### Issue: "Connection refused" (port 8443)

**Cause:** Container not running or port conflict

**Fix:**
```bash
# Check if container is running
docker compose ps

# Check if port is in use
lsof -i :8443

# If in use, kill conflicting process or change port in docker-compose.yml
# ports:
#   - "8444:8443"  # Map to different host port
```

### Issue: "Health check failed"

**Cause:** Controller still initializing or configuration issue

**Fix:**
```bash
# Check controller logs
docker logs ixia-c-controller -f

# Wait longer for startup (up to 30 seconds)
# Increase healthcheck retries in docker-compose.yml:
# healthcheck:
#   retries: 5  (default: 3)
```

### Issue: Traffic engine can't connect to controller

**Cause:** Network connectivity issue between containers

**Fix:**
```bash
# Verify network exists
docker network inspect ixia-c-net

# Check traffic engine logs
docker logs ixia-c-traffic-engine-1 -f

# Rebuild network
docker compose down
docker compose up -d
```

### Issue: Snappi connection error

**Cause:** Snappi SDK version mismatch or TLS issue

**Fix:**
```bash
# Update snappi
pip install --upgrade snappi

# Verify version
pip show snappi
# Should be >= 0.10.0

# Test connectivity with verify script
python verify_ixia_c.py --verbose
```

### Issue: Port assignment fails in test script

**Cause:** Port location format incorrect in infrastructure.yaml

**Fix:**
```bash
# Port location depends on traffic engine
# Common formats:
#   "1/1" (interface 1, port 1)
#   "eth1" (device name)
#   "p1" (logical name)

# Check actual port names from traffic engine
docker exec ixia-c-traffic-engine-1 \
  traffic-engine --info

# Update infrastructure.yaml with correct location
```

### Issue: BGP/ISIS protocols not starting

**Cause:** Protocol engine not deployed

**Fix:**
Add protocol-engine to docker-compose.yml:

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

Then redeploy:

```bash
docker compose down
docker compose up -d
```

### Issue: Containerlab node fails to start

**Cause:** Image not found or resource constraints

**Fix:**
```bash
# Check image availability
sudo clab pull -t topology.clab.yml

# Check resource availability
free -h
df -h

# Increase system limits if needed
ulimit -n 65535  # file descriptors
```

---

## Integration Workflow

```
┌─────────────────────────────────────────┐
│ ixia-c-deployment (this skill)          │
│ ↓ Setup infrastructure                  │
│ docker compose up -d or clab deploy     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ otg-config-generator or                 │
│ ixnetwork-to-keng-converter             │
│ ↓ Create OTG configuration              │
│ bgp_config.json                         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ snappi-script-generator                 │
│ ↓ Generate test script                  │
│ test_bgp.py                             │
└─────────────────────────────────────────┘
                    ↓
        python test_bgp.py
            ↓ Test Results
        test_report_YYYYMMDD_HHMMSS.json
```

---

## Reference

**GitHub Repositories:**
- [Ixia-c](https://github.com/open-traffic-generator/ixia-c) — Main repository
- [OTG Examples](https://github.com/open-traffic-generator/otg-examples) — Lab examples
- [Ixia-c Operator](https://github.com/open-traffic-generator/ixia-c-operator) — Kubernetes operator

**Documentation:**
- [OTG API Specification](https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/open-traffic-generator/models/main/yaml/otg.yaml)
- [Containerlab Documentation](https://containerlab.dev/)
- [Snappi SDK](https://github.com/open-traffic-generator/snappi)

**Image Registry:**
- `ghcr.io/open-traffic-generator/ixia-c-controller`
- `ghcr.io/open-traffic-generator/ixia-c-traffic-engine`
- `ghcr.io/open-traffic-generator/ixia-c-protocol-engine`
- `ghcr.io/open-traffic-generator/ixia-c-one`

---

## Files

- `SKILL.md` — Comprehensive deployment guide with all methods
- `README.md` — This file (quick start + troubleshooting)

---

## Next Steps

1. **Request deployment** — Use `/ixia-c-deployment` skill
2. **Deploy infrastructure** — `docker compose up -d` or `clab deploy`
3. **Verify setup** — Run verification script or cURL test
4. **Create test config** — Use `/otg-config-generator` or `/ixnetwork-to-keng-converter`
5. **Generate test script** — Use `/snappi-script-generator`
6. **Execute test** — `python test_xxx.py`

---

**Status**: ✅ Production-Ready | **Version**: 1.0 | **Last Updated**: 2026-03-17
