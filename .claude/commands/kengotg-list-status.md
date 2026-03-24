---
name: kengotg-list-status
description: Show all running Docker containers and network interfaces (veth, bridges, etc.)
disable-model-invocation: false
allowed-tools: ["Bash"]
---

# List Status — Docker Containers & Network Interfaces

Display the current state of Docker containers and network interfaces used by Ixia-c deployments.

## What This Command Shows

### Part 1: Docker Containers

List all running and stopped containers, with special highlighting for Ixia-c/KENG/OTG containers.

```bash
echo "=== Running Docker Containers ==="
sudo docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== All Containers (including stopped) ==="
sudo docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Ixia-c/KENG/OTG Containers Only ==="
sudo docker ps -a --filter "name=ixia-c" --filter "name=keng" --filter "name=clab-" --filter "name=otgen" \
  --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

### Part 2: Network Interfaces

Show all network interfaces, with focus on veth pairs used by tests.

```bash
echo ""
echo "=== All Network Interfaces ==="
ip link show | grep -E "^[0-9]+:|veth|br|docker" || echo "(none)"

echo ""
echo "=== veth Pairs (OTG Test Interfaces) ==="
ip link show type veth | awk 'NR % 2 == 1 {print}' || echo "(none)"

echo ""
echo "=== Bridge Interfaces ==="
ip link show type bridge || echo "(none)"
```

### Part 3: Port Usage

Check if common test ports are in use.

```bash
echo ""
echo "=== Port Status ==="
echo "Port 8443 (Ixia-c Controller):"
lsof -i :8443 2>/dev/null || echo "  (free)"

echo "Port 5555 (Traffic Engine):"
lsof -i :5555 2>/dev/null || echo "  (free)"

echo "Port 40051 (gRPC):"
lsof -i :40051 2>/dev/null || echo "  (free)"
```

---

## Usage

```
/kengotg-list-status
```

No arguments needed. Displays all three sections (containers, interfaces, ports).

---

## Interpretation Guide

### Docker Containers Section

**Status meanings:**
- `Up X minutes` — Container is running
- `Exited (X)` — Container stopped (X = exit code)
- `Restarting` — Container is in restart loop (indicates a crash)

**Common Ixia-c containers:**
- `keng-controller` — Control plane (orchestration API)
- `ixia-c-te-*` — Traffic engine (packet generation/capture)
- `ixia-c-pe-*` — Protocol engine (BGP, OSPF, etc.)
- `ixia-c-one` — All-in-one bundle (Containerlab deployments)
- `clab-<topo>-*` — Containerlab-managed containers (nodes in topology)

### Network Interfaces Section

**Interface types:**
- `veth*` — Virtual Ethernet pair (connects container to host/bridge)
- `docker*` — Docker bridge networks
- `br*` — Linux bridge (for Containerlab topologies)

**Example veth names:**
- `veth-a`, `veth-b` — OTG test pairs
- `veth0`, `veth1`, etc. — Numbered pairs (Docker Compose)

### Port Status Section

**Expected open ports (when running):**
- `8443/tcp` — Ixia-c controller REST API
- `5555/tcp` — Traffic engine gRPC (internal)
- `40051/tcp` — Controller gRPC

If ports show `(free)`, infrastructure is not running.

---

## When to Use

- **Troubleshooting:** Verify containers are running and ports are open
- **Status check:** Before starting a new test, confirm environment state
- **Cleanup verification:** After `/kengotg-cleanup`, verify all containers/interfaces removed
- **Multi-deployment:** Check which containers are running when testing multiple topologies

---

## Common Scenarios

### Scenario: All clean (no containers, no veth)
```
=== Ixia-c/KENG/OTG Containers Only ===
(none)

=== veth Pairs (OTG Test Interfaces) ===
(none)

Port 8443: (free)
```
✓ Ready for fresh deployment

---

### Scenario: Docker Compose running
```
=== Ixia-c/KENG/OTG Containers Only ===
keng-controller    Running    0.0.0.0:8443->8443/tcp
ixia-c-te-1        Running
ixia-c-pe-1        Running

=== veth Pairs ===
veth-a, veth-b     (present)

Port 8443: ixia-c (controller)
```
✓ Docker Compose deployment active

---

### Scenario: Containerlab running
```
=== Ixia-c/KENG/OTG Containers Only ===
clab-bgp-ixia-c-one    Running
clab-bgp-dut1          Running
clab-bgp-dut2          Running

=== Bridge Interfaces ===
clab-bgp (bridge)

Port 8443: ixia-c-one
```
✓ Containerlab topology active

---

## Troubleshooting

**Q: Containers showing "Restarting" or "Exited"**
→ Check logs: `docker logs <container-name>`
→ Common causes: port conflicts, config errors, permission issues

**Q: veth pairs present but containers not running**
→ Dangling interfaces (incomplete cleanup)
→ Run `/kengotg-cleanup` to fully remove

**Q: Port 8443 shows in use but no container**
→ Stale process holding the port
→ Kill: `sudo lsof -ti :8443 | xargs kill -9`

---

## Related Commands

- `/kengotg-cleanup` — Remove containers, interfaces, and reset to clean state
- `/kengotg-deploy-ixia` — Deploy infrastructure (Docker Compose or Containerlab)
- `/kengotg-create-test` — Full test pipeline including infrastructure
