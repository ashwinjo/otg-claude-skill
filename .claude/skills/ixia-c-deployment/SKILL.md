---
name: ixia-c-deployment
description: |
  Deploy and configure Ixia-c containerized traffic generator for OTG testing.
  Use this skill whenever you need to set up Ixia-c infrastructure before running tests.
  Covers Docker Compose (simple labs) and Containerlab (network topology labs).
  Include ixia-c-one, controller, traffic-engine, and protocol-engine setup.
---

# Ixia-c Deployment — Entry Point

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
| Traffic-only b2b, Docker | **Docker Compose — B2B** | `ref-docker-topologies.md` → Type dp |
| Protocols (BGP/ISIS) b2b, Docker | **Docker Compose — CP+DP** | `ref-docker-topologies.md` → Type cpdp |
| LAG testing, Docker | **Docker Compose — LAG** | `ref-docker-topologies.md` → Type lag |
| Simple b2b or DUT lab, Containerlab | **ixia-c-one** | `ref-containerlab-topologies.md` → Type A |
| Custom TE/PE versions, Containerlab | **Per-component clab** | `ref-containerlab-topologies.md` → Type B |
| Kubernetes / KNE | **Ixia-c Operator / KNE** | See Reference links below |

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

```bash
# Docker Compose
sudo docker compose ps
curl -sk https://localhost:8443/config   # returns {}

# Containerlab — get node IP first
sudo containerlab inspect -t topo.yml
curl -sk https://<node-ip>:8443/config
```

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
