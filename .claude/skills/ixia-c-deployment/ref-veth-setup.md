# Reference: veth Pair Setup for Ixia-c B2B
# Source: open-traffic-generator/conformance/do.sh

In DP-only deployments (`--net=host`), veth pairs live on the host network.
In CP+DP deployments, veth pairs are created on the host then pushed into
individual container network namespaces.

---

## Create a veth pair (host)

```sh
sudo ip link add veth-a type veth peer name veth-z
sudo ip link set veth-a up
sudo ip link set veth-z up
```

To tear down (only need to delete one end — peer is removed automatically):
```sh
sudo ip link delete veth-a
```

Standard veth names used in upstream conformance tests:
- Simple b2b: `veth-a` ↔ `veth-z`
- LAG member ports: `veth-b`, `veth-c` (port A side), `veth-y`, `veth-x` (port Z side)

---

## Push a veth interface into a container namespace (CP+DP only)

When traffic engines have their own network namespace (not `--net=host`),
the veth interface must be moved into the container's netns after the veth
pair is created on the host.

```sh
# Helper: get container ID and PID
CID=$(docker inspect --format="{{json .Id}}" <container-name> | cut -d\" -f2)
CPID=$(docker inspect --format="{{json .State.Pid}}" <container-name> | cut -d\" -f2)

# Move interface into container's network namespace
sudo mkdir -p /var/run/netns
sudo ln -s /proc/${CPID}/ns/net /var/run/netns/${CID}
sudo ip link set <ifc-name> netns ${CID}
sudo ip netns exec ${CID} ip link set <ifc-name> name <ifc-name>
sudo ip netns exec ${CID} ip -4 addr add 0/0 dev <ifc-name>
sudo ip netns exec ${CID} ip -4 link set <ifc-name> up

# Cleanup symlink
sudo rm -rf /var/run/netns/${CID}
```

For b2b CP+DP, do this for both sides:
```sh
# push veth-a into traffic engine A's namespace
push_ifc_to_container veth-a ixia-c-traffic-engine-veth-a

# push veth-z into traffic engine Z's namespace
push_ifc_to_container veth-z ixia-c-traffic-engine-veth-z
```

**Important:** Start containers with `WAIT_FOR_IFACE=Yes` so the traffic engine
waits up to 2 minutes for its interface to appear after the push.

---

## DP-only vs CP+DP interface setup summary

| Mode   | Veth location     | Engine network mode | Interface push needed? |
|--------|-------------------|---------------------|------------------------|
| dp     | Host netns        | `--net=host`        | No — engine sees host  |
| cpdp   | Container netns   | Default bridge      | Yes — push after start |
