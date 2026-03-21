---
name: deploy-ixia
description: Quick Ixia-c deployment
disable-model-invocation: false
allowed-tools: []
---

# Deploy-Ixia — Quick Infrastructure Deployment

Rapidly deploy Ixia-c (containerized traffic generator) for your test environment.

## Quick Start

Deploy Ixia-c in seconds:

```
/deploy-ixia
Deploy Ixia-c with Docker Compose for BGP testing
```

You get infrastructure files and port mappings ready for testing.

---

## Deployment Options

### Docker Compose (Simple, Single-Host)
```
/deploy-ixia
Docker Compose deployment for 2-port BGP test
```

**Best for:**
- POCs and demos
- Single-host labs
- 2-10 ports
- Quick setup

**Outputs:**
- `docker-compose-bgp-cpdp.yml`
- `setup-ixia-c-bgp.sh`
- Port mapping JSON

### Containerlab (Complex, Multi-Host)
```
/deploy-ixia
Containerlab topology with 8 ports, BGP + OSPF
```

**Best for:**
- Production labs
- Multi-host setups
- 20+ ports
- Full network simulation

**Outputs:**
- `topo.clab.yml`
- Container definitions
- Port mapping JSON

---

## Usage Patterns

### Basic BGP Setup
```
/deploy-ixia
Deploy Ixia-c with Docker Compose
Protocol: BGP
Ports: 2
```

### Multi-Protocol Setup
```
/deploy-ixia
Deploy Ixia-c for BGP + OSPF + LACP testing
Method: Docker Compose
Ports: 4
```

### Containerlab with Network Topology
```
/deploy-ixia
Deploy Ixia-c with Containerlab
Topology: Multi-host BGP convergence
Ports: 8
```

---

## What You Get

✓ Infrastructure manifest (docker-compose.yml or topo.clab.yml)
✓ Setup script with automation
✓ Port mapping (for next steps)
✓ Controller URL and credentials
✓ Deployment guide with verification steps

---

## Deployment Steps

### 1. Generate Infrastructure
```bash
/deploy-ixia
```

### 2. Deploy (Docker Compose)
```bash
docker-compose -f docker-compose-bgp-cpdp.yml up -d
```

Or run the automated script:
```bash
bash setup-ixia-c-bgp.sh
```

### 3. Verify Health
```bash
# Check controller
curl -k https://localhost:8443/config

# List ports
docker ps | grep ixia
```

### 4. Get Port Mapping
```bash
# From output or port_mapping.json
# te1 → veth-a
# te2 → veth-z
```

### 5. Use in Next Steps
```bash
/otg-gen
Create BGP test (controller at localhost:8443)
```

---

## Infrastructure Architecture

**Docker Compose (5 services):**
```
┌─────────────────────────────────┐
│ keng-controller (Control Plane)  │
├─────────────────────────────────┤
│ TE-A (Traffic Engine A)          │
│ TE-Z (Traffic Engine Z)          │
├─────────────────────────────────┤
│ PE-A (Protocol Engine A)         │
│ PE-Z (Protocol Engine Z)         │
└─────────────────────────────────┘
```

**Networking:**
- veth-a ↔ veth-z (veth pairs for traffic)
- Controller on localhost:8443
- Protocol engines in shared namespaces

---

## Port Mapping Example

```json
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
      "container": "ixia-c-traffic-engine-a",
      "ip": "172.18.0.2",
      "data_port": 5555
    },
    "veth-z": {
      "container": "ixia-c-traffic-engine-z",
      "ip": "172.18.0.3",
      "data_port": 5555
    }
  }
}
```

---

## Verification Checklist

After deployment:

```
✓ Docker containers running (docker ps)
✓ Controller responsive (curl -k https://localhost:8443)
✓ Traffic engines discoverable
✓ Port connectivity verified
✓ Port mapping JSON generated
```

---

## Common Issues & Solutions

**Docker daemon not running:**
```bash
# Start Docker
docker daemon
# or on Mac: open -a Docker
```

**Port already in use:**
```bash
# Check what's using port 8443
lsof -i :8443
# Kill and retry deployment
```

**Insufficient resources:**
```bash
# Check Docker disk space
docker system df
# Prune if needed
docker system prune
```

**Network issues:**
```bash
# Verify veth pairs created
ip link show | grep veth
# Check Docker network
docker network ls
```

---

## Next Steps

1. **Verify deployment** — Check controller health
2. **Create OTG config** — Use `/otg-gen` with port mapping
3. **Generate test script** — Use `/snappi-script`
4. **Run test** — Execute Python script

---

## Cleanup

When done testing:

```bash
# Stop containers (Docker Compose)
docker-compose -f docker-compose-bgp-cpdp.yml down

# Remove veth pairs (if using scripts)
bash setup-ixia-c-bgp.sh clean
```

---

## See Also

- `/otg-gen` — Generate OTG config using port mapping
- `/snappi-script` — Create executable test script
- `/show-skills` — Skill overview
- `/examples` — More deployment examples
