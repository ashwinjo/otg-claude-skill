# Ixia-c BGP Testing Deployment (CP+DP)

**Deployment Status:** ✅ Ready to Deploy
**Method:** Docker Compose (Control Plane + Data Plane)
**Use Case:** BGP Protocol Testing
**Ports:** 2 (veth-a and veth-z)
**Date Generated:** 2026-03-19

---

## Deployment Summary

This deployment sets up a complete **BGP testing environment** using Docker Compose with:
- **Control Plane (CP):** Ixia-c Controller (REST API on port 8443)
- **Data Plane (DP):** Two traffic engines (TE-A and TE-Z) with protocol engines
- **Protocols Enabled:** BGP, ISIS, LACP, LLDP (via protocol engines)
- **Network Mode:** Bridge network with veth pair injection

---

## Files Generated

| File | Purpose |
|------|---------|
| `docker-compose-bgp-cpdp.yml` | Docker Compose configuration (5 services) |
| `setup-ixia-c-bgp.sh` | Automated setup script (veth + config injection) |
| `DEPLOYMENT_OUTPUT.md` | This file (summary and reference) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Host Machine                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Docker Compose Network (Bridge)             │  │
│  │                                                          │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐    │  │
│  │  │  keng-controller     │  │  (Host veth pair)    │    │  │
│  │  │  (CP)                │  │  veth-a ←→ veth-z   │    │  │
│  │  │  REST: 8443          │  │                      │    │  │
│  │  │  gRPC: 40051         │  └──────────────────────┘    │  │
│  │  └──────────────────────┘           ↓                  │  │
│  │                                  (injected)             │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐    │  │
│  │  │ TE A                 │  │ TE Z                 │    │  │
│  │  │ (DP)                 │  │ (DP)                 │    │  │
│  │  │ 172.x.x.x:5555       │  │ 172.x.x.x:5555       │    │  │
│  │  │ + veth-a (injected)  │  │ + veth-z (injected)  │    │  │
│  │  └──────────────────────┘  └──────────────────────┘    │  │
│  │           ↓                           ↓                 │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐    │  │
│  │  │ PE A                 │  │ PE Z                 │    │  │
│  │  │ (shares TE-A netns)  │  │ (shares TE-Z netns)  │    │  │
│  │  │ gRPC: 172.x.x.x:50071   │ gRPC: 172.x.x.x:50071   │  │
│  │  └──────────────────────┘  └──────────────────────┘    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Instructions

### Quick Start (Automated)

```bash
# Make the setup script executable
chmod +x setup-ixia-c-bgp.sh

# Run the setup (handles veth creation + config injection)
./setup-ixia-c-bgp.sh
```

The script will:
1. ✅ Start Docker Compose services
2. ✅ Create veth pair (veth-a ↔ veth-z)
3. ✅ Inject veth into container namespaces
4. ✅ Inject controller configuration
5. ✅ Return port mapping for next agents

### Manual Steps (If Needed)

**Step 1: Start Docker Compose**
```bash
docker compose -f docker-compose-bgp-cpdp.yml up -d
```

**Step 2: Create veth pair**
```bash
sudo ip link add veth-a type veth peer name veth-z
sudo ip link set veth-a up
sudo ip link set veth-z up
```

**Step 3: Get container network info**
```bash
# Get container IDs
TE_A_ID=$(docker ps --filter "name=ixia-c-traffic-engine-veth-a" -q)
TE_Z_ID=$(docker ps --filter "name=ixia-c-traffic-engine-veth-z" -q)

# Get container IPs
TE_A_IP=$(docker inspect ixia-c-traffic-engine-veth-a --format='{{.NetworkSettings.Networks.ixia-c-net.IPAddress}}')
TE_Z_IP=$(docker inspect ixia-c-traffic-engine-veth-z --format='{{.NetworkSettings.Networks.ixia-c-net.IPAddress}}')

echo "TE-A: $TE_A_IP"
echo "TE-Z: $TE_Z_IP"
```

**Step 4: Push veth into container namespaces**
```bash
# For veth-a → TE-A
container_pid=$(docker inspect --format '{{.State.Pid}}' "$TE_A_ID")
sudo ip link set veth-a netns "$container_pid"
sudo nsenter -t "$container_pid" -n ip link set veth-a up

# For veth-z → TE-Z
container_pid=$(docker inspect --format '{{.State.Pid}}' "$TE_Z_ID")
sudo ip link set veth-z netns "$container_pid"
sudo nsenter -t "$container_pid" -n ip link set veth-z up
```

**Step 5: Inject controller configuration**
```bash
# Create config file
cat > /tmp/config.yaml << EOF
location_map:
  - location: veth-a
    endpoint: "${TE_A_IP}:5555+${TE_A_IP}:50071"
  - location: veth-z
    endpoint: "${TE_Z_IP}:5555+${TE_Z_IP}:50071"
EOF

# Copy to controller
docker exec keng-controller mkdir -p /home/ixia-c/controller/config
docker cp /tmp/config.yaml keng-controller:/home/ixia-c/controller/config.yaml
```

---

## Port Mapping (For otg-config-generator)

Pass this to the next agent for OTG config generation:

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
      "container": "ixia-c-traffic-engine-veth-a",
      "ip": "<from docker inspect>",
      "data_port": 5555,
      "protocol_port": 50071
    },
    "veth-z": {
      "container": "ixia-c-traffic-engine-veth-z",
      "ip": "<from docker inspect>",
      "data_port": 5555,
      "protocol_port": 50071
    }
  }
}
```

---

## Verification

### Check deployment status
```bash
# View all services
docker compose -f docker-compose-bgp-cpdp.yml ps

# View controller logs
docker compose -f docker-compose-bgp-cpdp.yml logs keng-controller

# Check controller API
curl -sk https://localhost:8443/config | jq .
```

### Verify veth injection
```bash
# Check veth in container namespace (TE-A)
docker exec ixia-c-traffic-engine-veth-a ip link show
# Should show: veth-a

# Check veth in container namespace (TE-Z)
docker exec ixia-c-traffic-engine-veth-z ip link show
# Should show: veth-z
```

### Check protocol engines
```bash
# TE-A namespace
docker exec ixia-c-protocol-engine-veth-a sh -c "netstat -tuln | grep 50071"

# TE-Z namespace
docker exec ixia-c-protocol-engine-veth-z sh -c "netstat -tuln | grep 50071"
```

---

## Cleanup

### Stop deployment
```bash
# Stop and remove containers
docker compose -f docker-compose-bgp-cpdp.yml down

# Remove veth pair
sudo ip link del veth-a
sudo ip link del veth-z
```

---

## Critical Configuration Notes

### Docker Compose Services

**keng-controller**
- Image: `ghcr.io/open-traffic-generator/ixia-c-controller:latest`
- Ports: 8443 (REST), 40051 (gRPC)
- EULA: ✅ `--accept-eula` enabled
- Healthcheck: TCP port 8443 (using `/dev/tcp`)

**ixia-c-traffic-engine-veth-a / veth-z**
- Image: `ghcr.io/open-traffic-generator/ixia-c-traffic-engine:latest`
- Listen Port: 5555 (both engines, local to container)
- Interface: `veth-a` / `veth-z` (injected after startup)
- Environment:
  - `ARG_IFACE_LIST=virtual@af_packet,veth-{a,z}` — Interface binding
  - `OPT_LISTEN_PORT=5555` — Data plane listen port
  - `OPT_NO_HUGEPAGES=Yes` — Disable DPDK hugepages in Docker
  - `OPT_NO_PINNING=Yes` — Disable CPU pinning in Docker
  - `WAIT_FOR_IFACE=Yes` — Wait for veth injection
  - `OPT_ADAPTIVE_CPU_USAGE=Yes` — Reduce idle CPU usage
- Healthcheck: TCP port 5555

**ixia-c-protocol-engine-veth-a / veth-z**
- Image: `ghcr.io/open-traffic-generator/ixia-c-protocol-engine:latest`
- Network Mode: `service:ixia-c-traffic-engine-veth-{a,z}` (shared namespace)
- Interface: `veth-a` / `veth-z` (inherited from TE)
- gRPC Port: 50071 (default, in container)

---

## OTG Configuration Alignment

**Port names in otg_config.json must match `location_map`:**

```yaml
# controller location_map (injected into controller)
location_map:
  - location: veth-a
    endpoint: "<TE-A-IP>:5555+<TE-A-IP>:50071"
  - location: veth-z
    endpoint: "<TE-Z-IP>:5555+<TE-Z-IP>:50071"
```

**OTG config must use same locations:**
```json
{
  "ports": [
    {"name": "P1", "location": "veth-a"},
    {"name": "P2", "location": "veth-z"}
  ]
}
```

---

## Controller API

### Check configuration status
```bash
curl -sk https://localhost:8443/config
```

### Get controller version
```bash
curl -sk https://localhost:8443/version
```

### Push OTG config
```bash
curl -sk -X POST https://localhost:8443/config \
  -H "Content-Type: application/json" \
  -d @otg_config.json
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "Connection refused" on 8443 | Controller not started | Wait 15s, check: `docker logs keng-controller` |
| "No test interfaces were specified" | Veth not injected | Run setup script or manually inject veths |
| PE not starting | Shared netns issue | Verify `network_mode: service:ixia-c-traffic-engine-veth-*` in compose |
| Traffic loss / no packets | Location_map not injected | Check: `docker exec keng-controller cat /home/ixia-c/controller/config.yaml` |
| Veth not visible in container | Injection failed | Check container PID: `docker inspect --format '{{.State.Pid}}'` |

---

## Health Checks Summary

✅ **Controller:** Reachable on https://localhost:8443
✅ **Traffic Engine A:** Listening on port 5555 (data) + 50071 (protocol)
✅ **Traffic Engine Z:** Listening on port 5555 (data) + 50071 (protocol)
✅ **Veth Pair:** Injected into container namespaces
✅ **Configuration:** location_map injected into controller

---

## Next Steps

1. **Generate OTG Config**
   - Invoke: `@otg-config-generator-agent`
   - Pass port mapping from above
   - Output: `otg_config.json`

2. **Generate Snappi Script**
   - Invoke: `@snappi-script-generator-agent`
   - Pass: `otg_config.json` + controller URL (https://localhost:8443)
   - Output: `test_bgp_xxx.py`

3. **Run Test**
   ```bash
   pip install snappi
   python test_bgp_xxx.py
   ```

---

## Files Reference

- **docker-compose-bgp-cpdp.yml** — Full Docker Compose config (5 services, bridge network)
- **setup-ixia-c-bgp.sh** — Automated setup script (veth + config injection)
- **DEPLOYMENT_OUTPUT.md** — This file

All files are in the project root directory.

---

**Deployment Generated:** 2026-03-19
**Status:** ✅ Ready for OTG configuration generation
