# Reference: Ixia-c Containerlab Topology Patterns
# Source: open-traffic-generator/otg-examples (clab/)

Containerlab topologies use two distinct ixia-c packaging options:

| Kind | Image | Use case |
|------|-------|----------|
| `keysight_ixia-c-one` | `ixia-c-one` | All-in-one: controller + TE + PE in one container. Simple, no config injection. |
| `linux` (per-component) | `keng-controller` + `ixia-c-traffic-engine` + `ixia-c-protocol-engine` | Separate containers. Matches the docker run cpdp pattern. |

---

## Type A: ixia-c-one (recommended for simple labs)

Single container bundles controller, traffic engine, and protocol engine.
No `location_map` config injection needed — the controller discovers ports via containerlab links.

**Port locations in OTG config** = the containerlab interface names (`eth1`, `eth2`, …)

### A1: B2B loopback (single ixia-c-one node, eth1 ↔ eth2)

```yaml
# topo.yml
name: ixcb2b
topology:
  nodes:
    ixia-c:
      kind: keysight_ixia-c-one
      image: ghcr.io/open-traffic-generator/ixia-c-one:1.48.0-5

    # Optional: Linux test runner container (runs snappi scripts)
    snappi:
      kind: linux
      image: snappi:local
      binds:
        - .:/otg

  links:
    # B2B: both ports on the same ixia-c-one node
    - endpoints: ["ixia-c:eth1", "ixia-c:eth2"]
```

Deploy / destroy:
```bash
sudo containerlab deploy -t topo.yml
sudo containerlab destroy -t topo.yml
```

Verify:
```bash
# Get ixia-c-one container IP
IXIA_IP=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' clab-ixcb2b-ixia-c)

# Check controller API (root is /config)
curl -sk https://${IXIA_IP}:8443/config
# Returns: {}
```

Infrastructure YAML for snappi-script-generator:
```yaml
controller:
  ip: "<ixia-c-one-container-ip>"
  port: 8443
  protocol: "https"

ports:
  - name: "P1"
    location: "eth1"   # containerlab interface name
  - name: "P2"
    location: "eth2"
```

### A2: B2B with external DUT

```yaml
name: ixia-c-dut-lab
topology:
  nodes:
    ixia-c:
      kind: keysight_ixia-c-one
      image: ghcr.io/open-traffic-generator/ixia-c-one:1.48.0-5

    dut:
      kind: ceos                        # or srl, crpd, linux, etc.
      image: ceos:4.29.1F

  links:
    - endpoints: ["ixia-c:eth1", "dut:eth1"]   # Ixia port 1 → DUT port 1
    - endpoints: ["ixia-c:eth2", "dut:eth2"]   # Ixia port 2 → DUT port 2
```

---

## Type B: Per-component containers (CP+DP, for protocol testing with DUT)

Matches the docker run cpdp pattern but expressed as a Containerlab topology.
Each traffic engine gets a protocol engine that shares its network namespace
(`network-mode: container:<te-name>`).

Containerlab manages veth links between nodes — no manual `push_ifc_to_container` needed.

### B1: CP+DP B2B with FRR DUT

```yaml
# topo.clab.yml
name: keng-frr
topology:
  nodes:
    ixc:
      kind: linux
      image: ghcr.io/open-traffic-generator/keng-controller:1.48.0-5
      network-mode: host
      cmd: --accept-eula --http-port 8443
      ports:
        - 8443:8443

    te1:
      kind: linux
      image: ghcr.io/open-traffic-generator/ixia-c-traffic-engine:1.8.0.245
      ports:
        - 5555:5555
        - 50071:50071
      env:
        OPT_LISTEN_PORT: "5555"
        ARG_IFACE_LIST: "virtual@af_packet,veth0"
        OPT_NO_HUGEPAGES: "Yes"
        OPT_NO_PINNING: "Yes"
        WAIT_FOR_IFACE: "Yes"           # required — clab creates veth after container starts

    pe1:
      kind: linux
      image: ghcr.io/open-traffic-generator/ixia-c-protocol-engine:1.00.0.507
      network-mode: container:te1       # shares te1 network namespace
      startup-delay: 5                  # wait for te1 to initialize first
      env:
        INTF_LIST: "veth0"

    dut:
      kind: linux
      image: quay.io/frrouting/frr:8.4.2
      binds:
        - ./frr/daemons:/etc/frr/daemons
        - ./frr/frr.conf:/etc/frr/frr.conf

    te2:
      kind: linux
      image: ghcr.io/open-traffic-generator/ixia-c-traffic-engine:1.8.0.245
      ports:
        - 5556:5556
        - 50072:50071
      env:
        OPT_LISTEN_PORT: "5556"
        ARG_IFACE_LIST: "virtual@af_packet,veth2"
        OPT_NO_HUGEPAGES: "Yes"
        OPT_NO_PINNING: "Yes"
        WAIT_FOR_IFACE: "Yes"

    pe2:
      kind: linux
      image: ghcr.io/open-traffic-generator/ixia-c-protocol-engine:1.00.0.507
      network-mode: container:te2
      startup-delay: 5
      env:
        INTF_LIST: "veth2"

  links:
    - endpoints: ["te1:veth0", "dut:veth1"]   # TE1 ↔ DUT port 1
    - endpoints: ["te2:veth2", "dut:veth3"]   # TE2 ↔ DUT port 2
```

**Controller location_map** must still be injected (see `ref-controller-config.md`).
The controller uses `network-mode: host` so it is on `localhost`; TE IPs are obtained
from the running containers.

---

## Containerlab tips

### Get node IPs after deploy
```bash
# Show all node IPs
sudo containerlab inspect -t topo.yml

# Or via docker
sudo docker inspect clab-<topo-name>-<node-name> \
  --format '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

### Image versions
- Pin image versions for reproducibility. Check latest at:
  https://github.com/open-traffic-generator/ixia-c/releases
- `ixia-c-one` bundles all components; its version must match across controller/TE/PE
  in separate-container deployments.

### ixia-c-one vs separate containers — decision guide

| Need | Use |
|------|-----|
| Simple traffic-only b2b | `ixia-c-one` (Type A) |
| BGP / ISIS / LACP with DUT | `ixia-c-one` (Type A) — PE is included |
| Custom TE/PE version control | Per-component (Type B) |
| High-scale multi-port | Per-component (Type B) |
| Fastest setup | `ixia-c-one` (Type A) |
