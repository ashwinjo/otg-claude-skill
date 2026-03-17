# Reference: Ixia-c Controller location_map Configuration
# Source: open-traffic-generator/conformance/do.sh

The controller needs a `location_map` config to know which traffic engine
handles each OTG port. This is injected via `docker cp` after containers start.

The OTG port `location` field in test scripts MUST match the `location` values
in this map — they are the human-readable port names (typically the veth name).

---

## location_map format

```yaml
# /home/ixia-c/controller/config/config.yaml  (inside controller container)
location_map:
  - location: <otg-port-name>      # matches port.location in OTG config
    endpoint: <te-address>          # how controller reaches the traffic engine
```

---

## Endpoint formats by topology type

### DP-only (traffic-only, `--net=host`)
```yaml
location_map:
  - location: veth-a
    endpoint: localhost:5555
  - location: veth-z
    endpoint: localhost:5556
```
- Controller and TEs all on host network → use `localhost`
- Port 5555 / 5556 = `OPT_LISTEN_PORT` of each traffic engine

### CP+DP (protocols enabled, container bridge network)
```yaml
location_map:
  - location: veth-a
    endpoint: "<te-a-ip>:5555+<te-a-ip>:50071"
  - location: veth-z
    endpoint: "<te-z-ip>:5555+<te-z-ip>:50071"
```
- `<te-ip>:5555` — traffic engine data plane port
- `<te-ip>:50071` — protocol engine gRPC port (protocol engine shares TE's netns)
- `+` separator joins the two endpoints into a single string

### LAG (multiple ports per engine)
```yaml
location_map:
  - location: veth-a
    endpoint: <te-a-ip>:5555;1+<te-a-ip>:50071   # port index 1
  - location: veth-b
    endpoint: <te-a-ip>:5555;2+<te-a-ip>:50071   # port index 2
  - location: veth-c
    endpoint: <te-a-ip>:5555;3+<te-a-ip>:50071   # port index 3
```
- `;N` suffix selects which logical port within a multi-port traffic engine
- The protocol engine endpoint (`+<te-ip>:50071`) is the same for all ports on one engine

---

## How to inject the config

```sh
# Write config locally
cat > ./config.yaml << EOF
location_map:
  - location: veth-a
    endpoint: localhost:5555
  - location: veth-z
    endpoint: localhost:5556
EOF

# Copy into running controller container
docker exec keng-controller mkdir -p /home/ixia-c/controller/config
docker cp ./config.yaml keng-controller:/home/ixia-c/controller/config/

# Clean up
rm -f ./config.yaml
```

**Timing:** Wait for traffic engine listen ports to be ready before injecting:
```sh
# Wait for TE to be ready (using nc)
until nc -z localhost 5555; do sleep 0.1; done
until nc -z localhost 5556; do sleep 0.1; done
```

---

## OTG config alignment

The `location` values in the map must match the `location` field on each port
in the OTG/snappi config:

```python
# Python snappi example
cfg = api.config()
p1 = cfg.ports.port(name="P1", location="veth-a")  # must match location_map
p2 = cfg.ports.port(name="P2", location="veth-z")  # must match location_map
```

```yaml
# infrastructure.yaml for snappi-script-generator
ports:
  - name: "P1"
    location: "veth-a"   # must match location_map
  - name: "P2"
    location: "veth-z"   # must match location_map
```

---

## Getting container IP (needed for CP+DP endpoint)

```sh
TE_A_IP=$(docker inspect --format="{{json .NetworkSettings.IPAddress}}" ixia-c-traffic-engine-veth-a | cut -d\" -f2)
TE_Z_IP=$(docker inspect --format="{{json .NetworkSettings.IPAddress}}" ixia-c-traffic-engine-veth-z | cut -d\" -f2)
```

For IPv6:
```sh
TE_A_IP6=$(docker inspect --format="{{json .NetworkSettings.GlobalIPv6Address}}" ixia-c-traffic-engine-veth-a | cut -d\" -f2)
# Wrap in brackets for IPv6 endpoint: "[${TE_A_IP6}]:5555+[${TE_A_IP6}]:50071"
```
