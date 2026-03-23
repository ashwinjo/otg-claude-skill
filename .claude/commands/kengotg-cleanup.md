---
name: kengotg-cleanup
description: Clean up all Ixia-c containers, veth pairs, and Containerlab topologies for a fresh state
disable-model-invocation: false
allowed-tools: ["Bash"]
---

# Cleanup — Reset Ixia-c Environment to Clean State

Remove all running Ixia-c containers, veth pairs, Docker networks, and Containerlab topologies so you start from a known clean state.

## What This Command Does

Runs a multi-step cleanup sequence. Each step is independent — failures in one step don't block the others.

> **Note:** This command does not modify `artifacts/` — your verified deployment configs and Snappi scripts are preserved across cleanups.

### Step 1: Stop and remove Ixia-c Docker containers

Find and remove all containers matching Ixia-c naming patterns:

```bash
# Stop and remove all ixia-c / keng containers
sudo docker ps -a --filter "name=ixia-c" --filter "name=keng" --filter "name=otgen" -q | xargs -r sudo docker rm -f 2>/dev/null

# Also catch containers from docker-compose deployments
for f in docker-compose*.yml docker-compose*.yaml; do
    [ -f "$f" ] && sudo docker compose -f "$f" down --remove-orphans 2>/dev/null
done
```

### Step 2: Destroy Containerlab topologies

```bash
# Find and destroy all clab topologies in current directory
for f in *.clab.yml topo.yml topo.yaml; do
    [ -f "$f" ] && sudo containerlab destroy -t "$f" --cleanup 2>/dev/null
done

# Also clean any remaining clab- prefixed containers
sudo docker ps -a --filter "name=clab-" -q | xargs -r sudo docker rm -f 2>/dev/null
```

### Step 3: Remove veth pairs

Delete all OTG-related veth interfaces (only need to delete one end — peer is removed automatically):

```bash
# Standard conformance veth names
for veth in veth-a veth-b veth-c veth-x veth-y veth-z; do
    sudo ip link delete "$veth" 2>/dev/null
done

# Also clean any veth0/veth1/veth2/veth3 that may have been created
for veth in veth0 veth1 veth2 veth3; do
    sudo ip link delete "$veth" 2>/dev/null
done
```

### Step 4: Clean up netns symlinks

```bash
# Remove any leftover netns symlinks from push_ifc_to_container
sudo rm -rf /var/run/netns/[0-9a-f]* 2>/dev/null
```

### Step 5: Remove generated files (optional — ask user first)

Only if user confirms:
```bash
# Remove generated infrastructure files
rm -f docker-compose*.yml docker-compose*.yaml
rm -f topo.yml topo.yaml *.clab.yml
rm -f setup-ixia-c*.sh
rm -f config.yaml
rm -f port_mapping.json
```

### Step 6: Verify clean state

```bash
# Verify no ixia-c / keng containers remain
echo "=== Remaining containers ==="
sudo docker ps -a --filter "name=ixia-c" --filter "name=keng" --filter "name=clab-" --filter "name=otgen" 2>/dev/null

# Verify no OTG veth pairs remain
echo "=== Remaining veth interfaces ==="
ip link show type veth 2>/dev/null | grep -E "veth-[a-z]|veth[0-9]" || echo "(none)"

# Verify port 8443 is free
echo "=== Port 8443 status ==="
lsof -i :8443 2>/dev/null || echo "(free)"

echo ""
echo "Cleanup complete. Environment is ready for fresh deployment."
```

## Usage

```
/kengotg-cleanup
```

No arguments needed. Runs all steps and reports results.

**Before cleanup, always confirm** with the user whether to also remove generated files (Step 5). Default: keep files, only remove containers and veth.

## When to Use

- Before a fresh `/kengotg-deploy-ixia` deployment
- After a test run to free resources
- When containers are in a bad state (port conflicts, stale processes)
- Before switching between Docker Compose and Containerlab deployments
- When troubleshooting "port already in use" or "container already exists" errors

## Safety

- Only targets Ixia-c/KENG/OTG containers (name filters: `ixia-c`, `keng`, `clab-`, `otgen`)
- Does NOT touch other Docker containers
- Veth cleanup only removes known OTG veth names (not arbitrary interfaces)
- Generated file removal requires explicit user confirmation
- Each step is independent — partial failures are reported but don't block other steps
