---
name: ixia-c-deployment
description: |
  Deploy and configure Ixia-c containerized traffic generator for OTG testing.
  Use this skill whenever you need to set up Ixia-c infrastructure before running tests.
  Covers Docker Compose (simple labs) and Containerlab (network topology labs).
  Include ixia-c-one, controller, traffic-engine, and protocol-engine setup.
---

# Ixia-c Deployment — Entry Point

> ⚠️ Read `fixes.md` in this directory before generating any output.

> 📁 Before generating any deployment config, read `artifacts/deployment/INDEX.md`.
> List existing verified configs to the user and ask: **reuse** or **regenerate**?
> When saving a new config: derive a descriptive filename (e.g. `bgp-2port-docker-compose.yml`),
> append a row to `artifacts/deployment/INDEX.md`. On name collision: ask overwrite or keep both.

## Step 0: Check if deployment already exists

**Always check for existing containers before deploying.**

```bash
# Check for running ixia-c containers
docker ps --filter "name=keng-controller\|ixia-c-traffic-engine\|ixia-c-protocol-engine\|ixia-c-one" --format "table {{.Names}}\t{{.Status}}"

# Or for Containerlab, check for running topology
sudo containerlab inspect -t topo.clab.yml 2>/dev/null | grep -i "^| Name" -A 20
```

**If containers/topology already exist:**
- ✅ Verify they match the requested use case (port count, protocol support, deployment method)
- ✅ If they match: Report "No deployment needed" + port mapping + controller URL
- ⚠️ If they don't match: Ask user if they want to reuse or rebuild
- 🗑️ Only proceed with teardown + rebuild if user explicitly requests it

**If no containers exist:** Proceed to Step 1

---

## Step 1: Read the relevant reference files

**Always read the applicable reference files before generating any configuration.**
They contain authoritative, battle-tested patterns from the upstream conformance harness.

| File | When to read it |
|------|-----------------|
| `ref-docker-topologies.md` | Any Docker (`docker run` or Compose) deployment |
| `ref-containerlab-topologies.md` | Any Containerlab deployment |
| `ref-controller-config.md` | Whenever a `location_map` must be injected (dp, cpdp, LAG, clab per-component) |
| `ref-veth-setup.md` | Whenever veth pairs must be created or pushed into container namespaces (cpdp, LAG) |

---

## Step 2: Choose a deployment method

| User need | Method | Reference |
|-----------|--------|-----------|
| Traffic-only b2b, Docker | **Docker Compose — B2B** (separate keng-controller + TE) | `ref-docker-topologies.md` → Type dp |
| Protocols (BGP/ISIS) b2b, Docker | **Docker Compose — CP+DP** (separate keng-controller + TE + PE) | `ref-docker-topologies.md` → Type cpdp |
| LAG testing, Docker | **Docker Compose — LAG** (separate keng-controller + multi-TE + PE) | `ref-docker-topologies.md` → Type lag |
| Simple b2b or DUT lab, Containerlab | **ixia-c-one** | `ref-containerlab-topologies.md` → Type A |
| Custom TE/PE versions, Containerlab | **Per-component clab** | `ref-containerlab-topologies.md` → Type B |
| Kubernetes / KNE | **Ixia-c Operator / KNE** | See Reference links below |

### ⚠️ CRITICAL: Never use ixia-c-one for Docker Compose

`ixia-c-one` is an all-in-one bundle optimized for Containerlab multi-node topologies. **DO NOT use it for Docker Compose deployments.**

**Why:** ixia-c-one has architectural constraints:
- Throughput capped at ~1.8 Gbps (not suitable for 10+ Gbps testing)
- No flow-level latency/loss metrics
- Suboptimal for standalone Docker Compose

**Always use separate containers for Docker Compose:**
```yaml
services:
  keng-controller:
    image: ghcr.io/open-traffic-generator/keng-controller:latest
    ...
  ixia-c-traffic-engine-1:
    image: ghcr.io/open-traffic-generator/ixia-c-traffic-engine:latest
    ...
  ixia-c-protocol-engine:
    image: ghcr.io/open-traffic-generator/ixia-c-protocol-engine:latest
    ...
```

See `ref-docker-topologies.md` for complete examples.

---

## Step 3: Critical image facts (apply to ALL Docker deployments)

These were validated by inspecting the actual images. Violating any of these causes silent or cryptic failures.

| Rule | Detail |
|------|--------|
| **No `entrypoint:` override** | Controller baked-in: `./bin/controller`. Traffic engine: `./entrypoint.sh`. Overriding either causes "executable not found" |
| **EULA required** | Add `command: --accept-eula` (Compose) or `cmd: --accept-eula` (clab) to controller. Without it the controller exits immediately |
| **No curl/wget in controller image** | Healthcheck must use: `["CMD", "bash", "-c", "echo > /dev/tcp/localhost/8443"]` |
| **Correct TE env vars** | See table below — wrong names are silently ignored |
| **API root is `/config`** | Not `/api/v1/config`. Empty config returns `{}` |

### Traffic engine environment variables

| Variable | Purpose | Value |
|----------|---------|-------|
| `ARG_IFACE_LIST` | Test interface(s) — **required** | `virtual@af_packet,<iface>` — space-separated for multiple |
| `OPT_LISTEN_PORT` | Listen port | `5555` / `5556` |
| `OPT_NO_HUGEPAGES` | Disable DPDK hugepages | `Yes` — always set in Docker |
| `OPT_NO_PINNING` | Disable CPU pinning | `Yes` — recommended in Docker |
| `OPT_ADAPTIVE_CPU_USAGE` | Reduce idle CPU | `Yes` — recommended |
| `WAIT_FOR_IFACE` | Wait for interface to appear | `Yes` — required in cpdp/clab when veth is added after start |
| `OPT_MEMORY` | DPDK memory (MB) | `1024` — for multi-port LAG engines |

**Do NOT use:** `LISTEN_PORT`, `VIRTUAL_INTERFACE`, `CONTROLLER` — not recognised by entrypoint.sh.

### Protocol engine environment variable

| Variable | Purpose | Value |
|----------|---------|-------|
| `INTF_LIST` | Interfaces PE manages | `veth-a` or `veth-a,veth-b,veth-c` for LAG |

Protocol engine must share the traffic engine's network namespace:
- Docker Compose: `network_mode: service:<te-service>`
- docker run: `--net=container:<te-container-name>`
- Containerlab: `network-mode: container:<te-node-name>`

---

## Step 4: Verify deployment

### Docker Compose Verification

```bash
# Check containers are running
sudo docker compose ps

# Verify controller is responding
curl -k https://localhost:8443/config   # returns {} if no config loaded
```

**Note:** The correct endpoint is `/config`, NOT `/api/v1/config`. The `-k` flag is required for self-signed certificates.

### Containerlab Verification

```bash
# Inspect deployed topology to get controller node IP
sudo containerlab inspect -t topo.yml

# Get the ixia-c container IP (if using ixia-c-one)
IXIA_IP=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' clab-<topo-name>-ixia-c)

# Verify controller is responding
curl -k https://${IXIA_IP}:8443/config   # returns {} if no config loaded
```

### Port Discovery

If containers use `network_mode: host`, Docker port mapping is empty. Discover actual ports from controller logs:

```bash
docker logs <controller-container-name> | grep -E "HTTPPort|GRPCPort|HTTPS Server|GRPC Server"
# Expected output:
# {"msg":"Build Details",...,"HTTPPort":8443,...}
# {"msg":"HTTPS Server started","addr":":8443",...}
# {"msg":"GRPC Server started","addr":"[::]:40051",...}
```

Default ports: **HTTPS 8443**, **GRPC 40051**

---

## Step 4.5: TLS and Certificates

Ixia-c uses **self-signed HTTPS certificates** by default in lab/test deployments.

### Verification with Self-Signed Certificates

When connecting via curl or any HTTPS client:
- **curl:** Use `-k` or `--insecure` flag
- **Python requests:** Pass `verify=False`
- **snappi:** Generated scripts automatically pass `verify=False` for self-signed certs

Example:
```bash
# CORRECT for self-signed certificates
curl -k https://localhost:8443/config

# WRONG — will fail TLS handshake
curl https://localhost:8443/config
# Error: TLS handshake error: unexpected EOF
```

### Production Deployments

For production deployments, replace self-signed certificates with CA-signed certificates:

```bash
# Generate CA-signed certificate (outside scope of this skill; coordinate with security/ops)
# Then mount into controller container:
docker run -v /path/to/certs/server.crt:/home/ixia-c/controller/certs/server.crt \
           -v /path/to/certs/server.key:/home/ixia-c/controller/certs/server.key \
           ...
```

Reference: [Ixia-c releases](https://github.com/open-traffic-generator/ixia-c/releases) — Deployment guide

---

## Step 5: Infrastructure YAML (for snappi-script-generator)

Port `location` values must match the `location` in the controller's `location_map`.

> **TLS note:** Ixia-c uses self-signed certificates by default. When connecting via snappi-script-generator, generated scripts must pass `verify=False` to `snappi.api()` (this is done automatically by the snappi-script-generator skill). For production deployments, replace with a CA bundle path.

| Deployment type | Port location format |
|-----------------|----------------------|
| Docker Compose B2B | `te1:5555` (Docker alias + listen port) |
| docker run dp (`--net=host`) | `veth-a` (veth name — used directly) |
| docker run cpdp | `veth-a` (mapped via location_map to TE IP) |
| Containerlab ixia-c-one | `eth1` (containerlab interface name) |

---

## Troubleshooting quick reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| `exec: "controller": executable file not found` | `entrypoint:` override in compose | Remove all `entrypoint:` lines |
| `EULA must be accepted` | Missing accept flag | Add `command: --accept-eula` |
| Healthcheck: `exec: "curl": executable file not found` | curl not in image | Use `/dev/tcp` healthcheck (see Step 3) |
| `No test interfaces were specified` | Wrong env var name | Use `ARG_IFACE_LIST` not `VIRTUAL_INTERFACE` |
| Protocols not starting | Protocol engine not deployed or wrong netns | PE must use `network_mode: container:<te>` + `INTF_LIST` |
| Port location not found | `location_map` not injected | See `ref-controller-config.md` |
| HTTP 500 `permission denied` on `/config` push | `docker cp` creates config.yaml as root (mode 600), controller process can't read it | After `docker cp`, run: `sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml` |
| BGP sessions flap / never establish in B2B | Connection collision — both emulated peers open TCP simultaneously | Set `"advanced": { "passive_mode": true }` on one peer in the OTG config so only one side initiates TCP |
| Snappi test connects to `localhost:8443` but gets Connection refused (Containerlab) | Containerlab runs ixia-c in isolated Docker network; `localhost:8443` resolves to host, not container | Discover container IP: `IXIA_IP=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' clab-<topo>-<node>)` and use `https://${IXIA_IP}:8443` in test script |
| curl to controller returns 404 `page not found` | Wrong endpoint — tried `/api/v1/config` instead of `/config` | Use correct endpoint: `curl -k https://localhost:8443/config` |
| curl to controller shows `TLS handshake error: unexpected EOF` in logs | Self-signed certificate rejected | Add `-k` or `--insecure` flag: `curl -k https://localhost:8443/config` |
| `docker inspect` shows empty `"Ports": {}` section for controller | Container uses `network_mode: host` (direct host network access, no port mapping) | Check controller logs for port configuration: `docker logs <container> \| grep "HTTPPort\|HTTPS Server"` (default: 8443) |

---

## Official Docker Image Paths (v1.48.0-5)

| Component | Image | Version |
|-----------|-------|---------|
| Controller | `ghcr.io/open-traffic-generator/keng-controller` | 1.48.0-5 |
| Traffic Engine | `ghcr.io/open-traffic-generator/ixia-c-traffic-engine` | 1.8.0.245 |
| Protocol Engine | `ghcr.io/open-traffic-generator/ixia-c-protocol-engine` | 1.00.0.507 |
| All-in-One | `ghcr.io/open-traffic-generator/ixia-c-one` | 1.48.0-5 |

**Note:** Controller is `keng-controller` (NOT `ixia-c-controller`). Check [releases](https://github.com/open-traffic-generator/ixia-c/releases) for newer versions.

---

## Reference links

- GitHub: https://github.com/open-traffic-generator/ixia-c
- OTG Examples: https://github.com/open-traffic-generator/otg-examples
- Conformance harness (do.sh): https://github.com/open-traffic-generator/conformance/blob/main/do.sh
- Ixia-c Operator (K8s): https://github.com/open-traffic-generator/ixia-c-operator
- KNE: https://github.com/openconfig/kne
- Snappi SDK: https://github.com/open-traffic-generator/snappi
