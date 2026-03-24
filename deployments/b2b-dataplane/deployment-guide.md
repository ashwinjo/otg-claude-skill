# Ixia-c B2B Dataplane Deployment Guide

## Overview

This deployment runs two Ixia-c traffic engines in a back-to-back (B2B) configuration connected via a Linux veth pair, managed by a single `keng-controller`. All containers run with `network_mode: host` — they share the host's network stack directly.

This topology is optimized for **maximum throughput testing** (100% line rate). There are no protocol engines, so it handles pure dataplane traffic (L2/L3 frames) with full flow-level metrics.

### Topology diagram

```
  Host network namespace
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │  keng-controller (:8443/:40051)                                     │
  │         │                                                           │
  │         ├── location_map: veth-a → localhost:5555                  │
  │         └── location_map: veth-z → localhost:5556                  │
  │                                                                     │
  │  ixia-c-te-a (:5555)         ixia-c-te-b (:5556)                   │
  │       │                             │                              │
  │     veth-a ──────────────────── veth-z                             │
  │       (B2B veth pair — traffic flows here)                          │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Linux host with Docker installed (Docker Compose plugin required)
- `sudo` / root access (needed for `ip link` commands)
- Ports **8443** and **40051** must be free on the host
- Ports **5555** and **5556** must be free on the host

---

## Quick Start

```bash
# 1. Clone / navigate to this directory
cd deployments/b2b-dataplane/

# 2. Deploy everything in one command
sudo ./setup-ixia-c-b2b.sh

# 3. Verify
curl -k https://localhost:8443/config
```

---

## Step-by-Step Deployment

### Step 1 — Create the veth pair

The veth pair is the virtual wire between the two traffic engines. It lives on the host network namespace because all containers use `network_mode: host`.

```bash
sudo ip link add veth-a type veth peer name veth-z
sudo ip link set veth-a up
sudo ip link set veth-z up

# Confirm
ip link show veth-a
ip link show veth-z
```

### Step 2 — Start containers

```bash
docker compose -f docker-compose-b2b-dataplane.yml up -d
```

Expected output:
```
[+] Running 3/3
 - Container keng-controller  Started
 - Container ixia-c-te-a      Started
 - Container ixia-c-te-b      Started
```

### Step 3 — Wait for readiness

```bash
# Controller healthcheck
docker inspect keng-controller --format='{{.State.Health.Status}}'
# Expected: healthy

# Traffic engine ports
nc -z localhost 5555 && echo "te-a ready"
nc -z localhost 5556 && echo "te-b ready"
```

### Step 4 — Inject location_map

The controller needs a `location_map` so it knows which traffic engine handles each OTG port location. This is a YAML file copied into the running controller container.

```bash
cat > /tmp/config.yaml <<EOF
location_map:
  - location: veth-a
    endpoint: localhost:5555
  - location: veth-z
    endpoint: localhost:5556
EOF

docker exec keng-controller mkdir -p /home/ixia-c/controller/config
docker cp /tmp/config.yaml keng-controller:/home/ixia-c/controller/config/config.yaml

# Fix permissions — docker cp sets mode 600 (root-only); controller runs as non-root
sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml

rm /tmp/config.yaml
```

### Step 5 — Validate

```bash
# Controller API — returns {} when no OTG config is loaded (expected)
curl -k https://localhost:8443/config

# Container status
docker compose -f docker-compose-b2b-dataplane.yml ps
```

---

## Port Mapping Summary

| Port name | OTG location | Traffic engine   | Listen port | Interface |
|-----------|-------------|------------------|-------------|-----------|
| `te_a`    | `veth-a`    | `ixia-c-te-a`    | 5555        | veth-a    |
| `te_b`    | `veth-z`    | `ixia-c-te-b`    | 5556        | veth-z    |

**Controller:** `https://localhost:8443`

---

## Using in OTG / Snappi Tests

OTG config port locations must match exactly:

```python
import snappi

api = snappi.api(location="https://localhost:8443", verify=False)
cfg = api.config()

# Port names can be anything; location must match location_map
p1 = cfg.ports.port(name="P1", location="veth-a")
p2 = cfg.ports.port(name="P2", location="veth-z")
```

The `verify=False` is required because the controller uses a self-signed certificate.

---

## Teardown

```bash
# Stop containers and remove veth pair
sudo ./setup-ixia-c-b2b.sh --teardown

# Or manually:
docker compose -f docker-compose-b2b-dataplane.yml down
sudo ip link delete veth-a   # peer veth-z is removed automatically
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `exec: "controller": executable file not found` | entrypoint override in compose | Remove all `entrypoint:` lines from compose file |
| Controller exits immediately | Missing EULA flag | Confirm `command: --accept-eula` is present |
| Healthcheck fails: `curl not found` | curl not in controller image | Use `/dev/tcp` healthcheck (already correct in this compose file) |
| `No test interfaces were specified` | Wrong env var name | Use `ARG_IFACE_LIST` not `VIRTUAL_INTERFACE` |
| Traffic engine not binding veth | veth pair not created before compose up | Create veth pair first (Step 1), then `compose up` |
| `curl https://localhost:8443/config` fails TLS | Self-signed cert | Use `curl -k https://localhost:8443/config` |
| HTTP 404 from controller | Wrong endpoint | Use `/config`, not `/api/v1/config` |
| `docker inspect` shows empty `Ports: {}` | Host network mode has no port mapping | Check ports via: `docker logs keng-controller \| grep "HTTPS Server"` |
| HTTP 500 permission denied on config push | docker cp creates file as root (mode 600) | Run `chmod 644` after `docker cp` (see Step 4) |

---

## Image Versions

| Component | Image | Tag |
|-----------|-------|-----|
| Controller | `ghcr.io/open-traffic-generator/keng-controller` | latest |
| Traffic Engine | `ghcr.io/open-traffic-generator/ixia-c-traffic-engine` | latest |

Pinned versions (v1.48.0-5 release):
- Controller: `1.48.0-5`
- Traffic Engine: `1.8.0.245`

To pin versions, replace `latest` with the specific tags in `docker-compose-b2b-dataplane.yml`.
