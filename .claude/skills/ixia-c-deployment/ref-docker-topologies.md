# Reference: Ixia-c Docker Topology Patterns
# Source: open-traffic-generator/conformance/do.sh

This file documents battle-tested docker run command patterns extracted directly
from the upstream conformance test harness. Use these as the authoritative source
when generating docker run or docker-compose deployments.

---

## Topology Types

| Type   | Use case                              | Network mode        | Protocol engine? |
|--------|---------------------------------------|---------------------|-----------------|
| `dp`   | Traffic-only, simple b2b              | `--net=host`        | No              |
| `cpdp` | Traffic + protocols (BGP, ISIS, LACP) | Bridge + container  | Yes             |
| `lag`  | Multi-port LAG testing                | Bridge + container  | Yes             |

---

## Type 1: DP-only B2B (`--net=host`)

The simplest deployment. All containers share the host network.
Veth pair is created on the host; traffic engines bind to them directly.

```sh
# 1. Create veth pair on host
sudo ip link add veth-a type veth peer name veth-z
sudo ip link set veth-a up
sudo ip link set veth-z up

# 2. Controller (host network)
docker run --net=host -d \
    --name=keng-controller \
    <controller-image> \
    --accept-eula \
    --disable-app-usage-reporter

# 3. Traffic engine A (binds to veth-a on host network)
docker run --net=host --privileged -d \
    --name=ixia-c-traffic-engine-veth-a \
    -e OPT_LISTEN_PORT="5555" \
    -e ARG_IFACE_LIST="virtual@af_packet,veth-a" \
    -e OPT_NO_HUGEPAGES="Yes" \
    -e OPT_NO_PINNING="Yes" \
    -e OPT_ADAPTIVE_CPU_USAGE="Yes" \
    <traffic-engine-image>

# 4. Traffic engine Z (binds to veth-z on host network)
docker run --net=host --privileged -d \
    --name=ixia-c-traffic-engine-veth-z \
    -e OPT_LISTEN_PORT="5556" \
    -e ARG_IFACE_LIST="virtual@af_packet,veth-z" \
    -e OPT_NO_HUGEPAGES="Yes" \
    -e OPT_NO_PINNING="Yes" \
    -e OPT_ADAPTIVE_CPU_USAGE="Yes" \
    <traffic-engine-image>

# 5. Inject location_map config into controller
# (see ref-controller-config.md for format)
```

**OTG port locations:** `veth-a` and `veth-z` (the veth names ARE the OTG port locations).

**Controller location_map** (dp-only):
```yaml
location_map:
  - location: veth-a
    endpoint: localhost:5555
  - location: veth-z
    endpoint: localhost:5556
```

---

## Type 2: CP+DP B2B (protocols enabled)

Traffic engine and protocol engine share a network namespace.
Veth pairs are pushed INTO the container namespace after startup.
`WAIT_FOR_IFACE=Yes` lets the TE wait for the interface to appear.

```sh
# 1. Controller (published ports, NOT --net=host)
docker run -d \
    --name=keng-controller \
    --publish 0.0.0.0:8443:8443 \
    --publish 0.0.0.0:40051:40051 \
    <controller-image> \
    --accept-eula \
    --disable-app-usage-reporter

# 2. Traffic engine A (own network namespace)
docker run --privileged -d \
    --name=ixia-c-traffic-engine-veth-a \
    -e OPT_LISTEN_PORT="5555" \
    -e ARG_IFACE_LIST="virtual@af_packet,veth-a" \
    -e OPT_NO_HUGEPAGES="Yes" \
    -e OPT_NO_PINNING="Yes" \
    -e WAIT_FOR_IFACE="Yes" \
    -e OPT_ADAPTIVE_CPU_USAGE="Yes" \
    <traffic-engine-image>

# 3. Protocol engine A — SHARES TE-A's network namespace
docker run --privileged -d \
    --net=container:ixia-c-traffic-engine-veth-a \
    --name=ixia-c-protocol-engine-veth-a \
    -e INTF_LIST="veth-a" \
    <protocol-engine-image>

# 4. Traffic engine Z (own network namespace)
docker run --privileged -d \
    --name=ixia-c-traffic-engine-veth-z \
    -e OPT_LISTEN_PORT="5555" \
    -e ARG_IFACE_LIST="virtual@af_packet,veth-z" \
    -e OPT_NO_HUGEPAGES="Yes" \
    -e OPT_NO_PINNING="Yes" \
    -e WAIT_FOR_IFACE="Yes" \
    -e OPT_ADAPTIVE_CPU_USAGE="Yes" \
    <traffic-engine-image>

# 5. Protocol engine Z — SHARES TE-Z's network namespace
docker run --privileged -d \
    --net=container:ixia-c-traffic-engine-veth-z \
    --name=ixia-c-protocol-engine-veth-z \
    -e INTF_LIST="veth-z" \
    <protocol-engine-image>

# 6. Create veth pair and push into container namespaces
sudo ip link add veth-a type veth peer name veth-z
sudo ip link set veth-a up
sudo ip link set veth-z up
# push_ifc_to_container — see ref-veth-setup.md
```

**Controller location_map** (cp+dp) — note `5555+50071` format:
```yaml
location_map:
  - location: veth-a
    endpoint: "<te-a-container-ip>:5555+<te-a-container-ip>:50071"
  - location: veth-z
    endpoint: "<te-z-container-ip>:5555+<te-z-container-ip>:50071"
```

---

## Type 3: B2B LAG (multiple ports per engine)

Each engine manages multiple veth interfaces (multi-port LAG).

```sh
# Traffic engine A — 3 ports for LAG
docker run --privileged -d \
    --name=ixia-c-traffic-engine-veth-a \
    -e OPT_LISTEN_PORT="5555" \
    -e ARG_IFACE_LIST="virtual@af_packet,veth-a virtual@af_packet,veth-b virtual@af_packet,veth-c" \
    -e OPT_NO_HUGEPAGES="Yes" \
    -e OPT_NO_PINNING="Yes" \
    -e WAIT_FOR_IFACE="Yes" \
    -e OPT_ADAPTIVE_CPU_USAGE="Yes" \
    -e OPT_MEMORY="1024" \
    <traffic-engine-image>

# Protocol engine A — lists all LAG interfaces
docker run --privileged -d \
    --net=container:ixia-c-traffic-engine-veth-a \
    --name=ixia-c-protocol-engine-veth-a \
    -e INTF_LIST="veth-a,veth-b,veth-c" \
    <protocol-engine-image>
```

**Controller location_map** (LAG — note `;1`, `;2`, `;3` port indices):
```yaml
location_map:
  - location: veth-a
    endpoint: <te-a-ip>:5555;1+<te-a-ip>:50071
  - location: veth-b
    endpoint: <te-a-ip>:5555;2+<te-a-ip>:50071
  - location: veth-c
    endpoint: <te-a-ip>:5555;3+<te-a-ip>:50071
  - location: veth-z
    endpoint: <te-z-ip>:5555;1+<te-z-ip>:50071
  - location: veth-y
    endpoint: <te-z-ip>:5555;2+<te-z-ip>:50071
  - location: veth-x
    endpoint: <te-z-ip>:5555;3+<te-z-ip>:50071
```
