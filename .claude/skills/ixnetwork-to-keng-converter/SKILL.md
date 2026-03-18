---
name: ixnetwork-to-keng-converter
description: |
  Convert IxNetwork test configurations to Open Traffic Generator (OTG/KENG) JSON format.

  Use this skill whenever you need to:
  - Convert IxNetwork RestPy code to OTG configuration
  - Convert IxNetwork JSON config files to OTG format
  - Check if an IxNetwork config can be migrated to KENG/ixia-c
  - Understand what IxNetwork features are/aren't supported in OTG
  - Get a detailed conversion report showing supported/unsupported features

  Automatically detects input format (Python code or JSON). Performs feasibility check first,
  lists unsupported features with severity levels (blocker vs workaround), then generates
  OTG configuration + detailed conversion report.
compatibility: []
---

## Overview

This skill converts IxNetwork test configurations to vendor-neutral OTG/KENG format. It handles:

- **Input detection**: Auto-detects RestPy code (Python) or IxNetwork JSON configs
- **Feasibility analysis**: Checks if conversion is possible before attempting it
- **Severity classification**: Lists unsupported features as blockers (prevents conversion) or workarounds (suggests fixes)
- **Dual output**: Produces both OTG JSON config and detailed conversion report

### MVP Support

**Fully supported features:**
- BGP (eBGP/iBGP peering, IPv4 unicast)
- Ethernet interfaces with MAC addresses
- IPv4 addressing (single addresses, gateways)
- VLANs (basic configuration)
- Traffic flows (bidirectional, port-based, IPv4/Ethernet headers)
- Port mapping and topology

**Partially supported / workarounds:**
- Multipliers (handled at runtime orchestration level, not config)
- Advanced BGP features (route filtering, redistribution) — use as manual post-config
- Increment address pools — use multiplier at runtime instead

**Unsupported (blockers):**
- OSPF, ISIS, RIP, other routing protocols
- LACP, LLDP (cannot be *converted* from IxNetwork, but can be *added natively* in OTG — see note below)
- Advanced traffic tracking (multicast, QoS, deep packet inspection)
- Stateful protocols (TCP, complex application layer)
- Device replication via multiplier (must be flattened into explicit device list)

> **Note on LACP/LLDP/ISIS:** These protocols cannot be auto-converted from IxNetwork format, but OTG *does* support them natively. If your IxNetwork config includes BGP + LLDP, this skill converts the BGP portion and flags LLDP as unsupported. You can then use `/otg-config-generator` to add LLDP or ISIS configuration to the converted OTG config. Example workflow:
> 1. `/ixnetwork-to-keng-converter` → converts BGP, flags LLDP as skipped
> 2. `/otg-config-generator` → "Add LLDP to this OTG config: [paste otg_config.json]"

---

## Usage

### Basic Workflow

1. **Provide IxNetwork input** — either:
   - Python code snippet (RestPy script)
   - IxNetwork JSON configuration file
   - Path to a .ipynb notebook or .py file

2. **Specify context** (optional but recommended):
   - What the test is trying to achieve (for better mapping)
   - Any known limitations or custom logic

3. **Skill processes**:
   - Detects input format
   - Parses IxNetwork structure
   - Checks feasibility → lists unsupported features with severity
   - If convertible: generates OTG JSON + conversion report
   - If not convertible: explains why and suggests alternatives

4. **Review outputs**:
   - `otg_config.json` — Ready-to-use OTG configuration
   - `conversion_report.md` — Summary of conversions, warnings, gaps

---

## Input Formats Recognized

### Format 1: Python RestPy Code

```python
# Example: IxNetwork RestPy setup
session_assistant = SessionAssistant(...)
ixnetwork = session_assistant.Ixnetwork

# Port mapping
portMap = session_assistant.PortMapAssistant()
portMap.Map(chassis_ip, CardId=9, PortId=2, Name="Port_1")

# Topology
topology = ixnetwork.Topology.add(Name="Topo1")
devgrp = topology.DeviceGroup.add(Name="DG1", Multiplier=2)
ethernet = devgrp.Ethernet.add(Name="Eth1")
ipv4 = ethernet.Ipv4.add(Name="Ipv41")
ipv4.Address.Increment(start_value="1.1.1.4", step_value="0.0.0.1")

# BGP
bgp = ipv4.BgpIpv4Peer.add(Name="BGPPeer1")
bgp.DutIp.Increment(start_value="1.1.1.1", step_value="0.0.0.1")
```

**How it's parsed:**
- `PortMapAssistant.Map()` → `ports[]`
- `Topology → DeviceGroup` → `devices[]`
- `Ethernet → Ipv4 → BgpIpv4Peer` → device hierarchy
- `TrafficItem` → `flows[]`

### Format 2: IxNetwork JSON Config

```json
{
  "tgenConfig": {
    "endpoint1": {
      "ixia-chassis-ip": "10.36.231.231",
      "ixia-chassis-card": "9",
      "ixia-chassis-port": "2",
      "ipv4": {
        "addressStartValue": "1.1.1.4",
        "gatewayStartValue": "1.1.1.1"
      },
      "bgp": {
        "localas2value": 101,
        "increment": "1.1.1.1"
      }
    },
    "endpoint2": { ... }
  }
}
```

**How it's parsed:**
- Endpoints → ports + devices
- ipv4 config → device_eth[] + ipv4_addresses[]
- bgp config → bgp[] + neighbors[]

### Format 3: File Paths

```
/path/to/config.ipynb          # Jupyter notebook (extracts code cells)
/path/to/test_script.py        # Python file
/path/to/config.json           # JSON file
```

---

## Conversion Process

### Step 1: Feasibility Check

Before attempting conversion, the skill:

1. **Scans input** for all IxNetwork objects and methods
2. **Maps to OTG support** — each IxNetwork concept has a mapping:
   - ✅ Fully supported
   - ⚠️ Partial (workaround available)
   - ❌ Unsupported (blocker)
3. **Classifies blockers**:
   - **Critical**: Protocol not supported (OSPF, ISIS) → conversion impossible
   - **Feature-level**: Advanced feature not in OTG (route filtering) → workaround
4. **Reports findings**:
   - All unsupported features listed with severity
   - Suggestions for workarounds or manual post-config
   - Decision: "Proceed with conversion" or "Cannot convert"

### Step 2: Feature Mapping

| IxNetwork Concept | OTG Mapping | Notes |
|---|---|---|
| SessionAssistant | (omitted) | OTG is API-agnostic |
| Topology | devices[] | Container for L2-L7 config |
| DeviceGroup | device instance | Single device per group (multiplier applied at runtime) |
| Multiplier | (omitted) | Handled by orchestrator, not config |
| Ethernet | device_eth[] | L2 interface with MAC |
| Ipv4 | ipv4_addresses[] | L3 addressing (single IP, not increment pool) |
| BgpIpv4Peer | bgp[] + neighbors[] | BGP protocol peering |
| NetworkGroup | network_group[] (optional) | Route advertisement |
| TrafficItem | flows[] | Bidirectional becomes 2 flows |
| Port (physical) | ports[] | Abstract port with location |

### Step 3: Generate OTG Configuration

Creates a valid OTG JSON with:
- `ports[]` — Test ports
- `devices[]` — Emulated routers/endpoints with L2/L3/L4 config
- `flows[]` — Traffic definitions
- `captures[]` (optional) — Packet capture points

### Step 4: Generate Conversion Report

Produces `conversion_report.md` with:
- **Summary**: What was converted, what wasn't
- **Supported features**: List of converted components
- **Partial conversions**: Features converted with limitations
- **Unsupported features**: What's missing and why
- **Workarounds**: How to handle unsupported features
- **Caveats**: Known differences between IxNetwork and OTG
- **Next steps**: How to use the OTG config with ixia-c or KENG

---

## Output Structure

### Success Case

```
otg_config.json          # Valid OTG configuration (ready to use)
conversion_report.md     # Detailed conversion summary
```

**otg_config.json** structure:
```json
{
  "ports": [
    { "name": "P1", "location": "P1" },
    { "name": "P2", "location": "P2" }
  ],
  "devices": [
    {
      "name": "device_P1",
      "device_eth": [ ... ],
      "bgp": [ ... ]
    }
  ],
  "flows": [ ... ]
}
```

**conversion_report.md** includes:
- Conversion summary (X features converted, Y warnings)
- Supported components (ports, devices, protocols, flows)
- Workarounds applied (e.g., "Multiplier=2 → create 2 explicit devices")
- Unsupported features (with blockers vs warnings)
- Usage instructions
- Example deployment with curl/Python

### Failure Case (Non-Convertible)

If conversion is impossible:

```
conversion_report.md     # Explains why, lists blockers
(no otg_config.json)
```

Report explains:
- Blocking unsupported features (e.g., "OSPF not supported in OTG")
- Why they prevent conversion
- Suggestions (switch to BGP, split into multiple tests, etc.)

---

## Examples

### Example 1: BGP Configuration ✅ Convertible

**Input** (IxNetwork Python code):
```python
# 2-port BGP test, bidirectional traffic
devgrp1.Ethernet.add(...).Ipv4.add(...).BgpIpv4Peer.add(...)
devgrp2.Ethernet.add(...).Ipv4.add(...).BgpIpv4Peer.add(...)
traffic_item = ixnetwork.Traffic.TrafficItem.add(BiDirectional=True, ...)
```

**Output** (OTG JSON + report):
```json
{
  "ports": [{"name": "P1", "location": "P1"}, {"name": "P2", "location": "P2"}],
  "devices": [
    {
      "name": "device_P1",
      "device_eth": [{"name": "eth1", "ipv4_addresses": [...]}],
      "bgp": [{"asn": 101, "neighbors": [...]}]
    },
    {
      "name": "device_P2",
      "device_eth": [{"name": "eth1", "ipv4_addresses": [...]}],
      "bgp": [{"asn": 102, "neighbors": [...]}]
    }
  ],
  "flows": [
    {"name": "flow_p1_to_p2", ...},
    {"name": "flow_p2_to_p1", ...}
  ]
}
```

**Report** highlights:
- ✅ BGP peering converted
- ✅ Bidirectional traffic mapped to 2 flows
- ⚠️ Multiplier=2 → created 2 explicit devices (expand before runtime)
- ✅ Ready to deploy

### Example 2: OSPF Configuration ❌ Not Convertible

**Input**:
```python
ospf = ipv4.OspfIpv4.add(...)
```

**Feasibility Check Output**:
```
❌ CONVERSION NOT POSSIBLE

Blockers:
- OSPF protocol (not supported in OTG)
  Reason: OTG MVP only supports BGP
  Severity: CRITICAL (prevents entire config conversion)

Suggestions:
1. If possible, switch test to BGP instead of OSPF
2. Keep IxNetwork test for OSPF, use OTG only for BGP tests
3. Check if ixia-c roadmap includes OSPF support
```

---

## Workflow: What to Do When

### When to use this skill:

1. **Migrating from IxNetwork to KENG/ixia-c**
   - You have working IxNetwork RestPy scripts
   - You want to move to vendor-neutral OTG format
   - Unclear what IxNetwork features KENG supports

2. **Understanding KENG capabilities**
   - What IxNetwork tests can run on KENG?
   - What features need to stay in IxNetwork?
   - Understand the conversion gaps

3. **Planning a multi-tool test strategy**
   - Some tests on IxNetwork (advanced features)
   - Some tests on KENG (basic protocol testing)
   - Skill helps identify the split

### When NOT to use:

- You need to run the test immediately (skill produces config, not execution)
- You need features not in MVP (OSPF, LACP, stateful protocols)
- You want to keep IxNetwork (no downside, but skill helps if you're considering a move)

---

## Common Patterns & Workarounds

### Pattern 1: Multiplier → Explicit Devices

**IxNetwork** (compact):
```python
devgrp = topology.DeviceGroup.add(Multiplier=2)
devgrp.Ethernet.add(...).Ipv4.add(start="1.1.1.0", step="0.0.0.1")
```

**OTG** (expanded):
```json
{
  "devices": [
    {"name": "device_1", "device_eth": [{"ipv4_addresses": [{"address": "1.1.1.0"}]}]},
    {"name": "device_2", "device_eth": [{"ipv4_addresses": [{"address": "1.1.1.1"}]}]}
  ]
}
```

**Why**: OTG is declarative; multiplier is orchestration. Expand at generation time or use multiplier in your test runner.

### Pattern 2: Bidirectional Traffic → Two Flows

**IxNetwork**:
```python
traffic_item.add(BiDirectional=True)
```

**OTG**:
```json
{
  "flows": [
    {"name": "flow_p1_to_p2", "tx_rx": {"port": {"tx_name": "P1", "rx_names": ["P2"]}}},
    {"name": "flow_p2_to_p1", "tx_rx": {"port": {"tx_name": "P2", "rx_names": ["P1"]}}}
  ]
}
```

**Why**: OTG requires explicit directional definitions. Easier to modify per-direction later.

### Pattern 3: Increment Pools → Runtime Multiplier

**IxNetwork**:
```python
ipv4.Address.Increment(start_value="10.10.0.0", step_value="0.0.1.0")  # with Multiplier=100
```

**OTG**:
```json
{
  "ipv4_addresses": [
    {"address": "10.10.0.0", "prefix": 24}
  ]
}
```

Then in your test runner:
```python
# Expand at test time:
for i in range(100):
    device = devices[0].copy()
    device['name'] = f"device_{i}"
    device['device_eth'][0]['ipv4_addresses'][0]['address'] = f"10.10.{i}.0"
```

**Why**: Config should be declarative; procedural expansion happens at runtime.

---

## Limitations & Caveats

1. **No runtime behavior** — OTG config defines static structure, not how tests run
   - Multipliers, timing, state machines → handle in test runner

2. **Session/API removed** — OTG is API-agnostic
   - SessionAssistant, IxNetwork SDK calls → implement in your test framework

3. **Stats collection different** — OTG metrics are different from IxNetwork
   - Re-tune assertions if migrating tests

4. **No advanced tracking** — OTG doesn't support IxNetwork's detailed flow tracking
   - sourceDestEndpointPair, encapsulation tracking → not available

5. **Protocol scale limits** — Different limits between IxNetwork and ixia-c
   - Test at target scale to verify

---

## Next Steps After Conversion

### 0. Deploy Ixia-c Infrastructure (if not already running)

Before deploying the config, ensure ixia-c is running. Use the `/ixia-c-deployment` skill:
```
/ixia-c-deployment
→ Docker Compose (simple b2b lab) or Containerlab (topology lab)
→ Controller available at https://localhost:8443
```

### 1. Validate the OTG Config

```bash
# Use Snappi SDK to validate
python -c "
from snappi import Api
config = open('otg_config.json').read()
api.set_config(config)
print('Config validated')
"
```

### 2. Deploy to KENG/ixia-c

```bash
# Example with curl
curl -X POST http://keng-ip/config \
  -H "Content-Type: application/json" \
  -d @otg_config.json
```

### 3. Execute Test

Use Snappi or raw REST to start protocols, traffic, and collect metrics.

### 4. Compare Results

Run the same test on both IxNetwork and OTG, compare:
- BGP session establishment time
- Traffic rates and latency
- Loss, jitter, reordering
- Throughput under load

---

## Reference: IxNetwork → OTG Mapping Table

| IxNetwork | OTG | Status |
|---|---|---|
| Topology | devices[] | ✅ |
| DeviceGroup | device | ✅ |
| Ethernet | device_eth[] | ✅ |
| Ipv4 | ipv4_addresses[] | ✅ |
| BgpIpv4Peer | bgp[] neighbors[] | ✅ |
| NetworkGroup | network_group[] | ⚠️ (optional) |
| TrafficItem | flows[] | ✅ |
| Port (phys) | ports[] | ✅ |
| Multiplier | (runtime) | ⚠️ (not in config) |
| Vlan | vlans[] | ✅ |
| OSPF | — | ❌ |
| ISIS | — | ❌ |
| LACP | — | ❌ |
| QoS marking | — | ❌ |

