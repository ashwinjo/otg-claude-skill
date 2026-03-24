---
name: kengotg-migrate-ix
description: Quick IxNetwork migration to OTG/KENG format (dispatches to ixnetwork-to-keng-converter-agent)
disable-model-invocation: false
allowed-tools: []
---

# Migrate-Ix — Quick IxNetwork Migration

Rapidly migrate IxNetwork test configurations to Open Traffic Generator (OTG/KENG) format.

## Agent Dispatch (REQUIRED)

**This command MUST dispatch to the `ixnetwork-to-keng-converter-agent` subagent.**

Do NOT execute the skill directly. Instead, use the Agent tool:

```
Agent tool call:
  subagent_type: ixnetwork-to-keng-converter-agent
  prompt: <forward the user's migration request, IxNetwork config, and any arguments>
  description: "Migrate IxNetwork to OTG"
```

The agent will invoke the `ixnetwork-to-keng-converter` skill internally, run feasibility analysis, and return the converted config + report.

**Hierarchy:** `/kengotg-migrate-ix` (command) → `ixnetwork-to-keng-converter-agent` (agent) → `ixnetwork-to-keng-converter` (skill)

---

## Quick Start

Migrate your IxNetwork config:

```
/migrate-ix
[paste your IxNetwork RestPy code or JSON config]
```

Get converted OTG config and feasibility report instantly.

---

## Input Formats

### IxNetwork RestPy Code
```python
ixnObj = IxNetwork()
ixnObj.connect('10.1.1.1', 443, 'admin', 'admin')
vport1 = ixnObj.Vport.add()
vport1.Name = 'Port1'
bgp1 = vport1.Protocols.Bgp.add()
bgp1.RouterId = '1.1.1.1'
bgp1.AsNumber = 65001
# ... more config
```

### IxNetwork JSON
```json
{
  "vports": [
    {"name": "Port1", "location": "10.1.1.1:1/1"},
    {"name": "Port2", "location": "10.1.1.1:1/2"}
  ],
  "protocols": [
    {"type": "BGP", "asNumber": 65001}
  ]
}
```

### Highlevel Description
```
BGP test with 2 ports, AS 65001 and AS 65002, 1000 pps bidirectional traffic
```

---

## What You Get

✓ **Feasibility Report** — % convertible (0-100%)
✓ **Supported Features** — ✓ what converts cleanly
✓ **Unsupported Features** — ✗ what needs workarounds
✓ **OTG Config** — Converted JSON (for supported features)
✓ **Conversion Mapping** — Table showing IxNetwork → OTG mapping

---

## Output Structure

```
conversion_report.md
├─ Feasibility Score: 85%
├─ Supported Features (85%)
│  ├─ BGP ✓
│  ├─ Traffic Flows ✓
│  └─ Basic Assertions ✓
├─ Unsupported Features (15%)
│  ├─ Advanced SLA Monitoring ✗ (Workaround: use basic metrics)
│  └─ Custom Encapsulation ✗
├─ Migration Risk: LOW
└─ Recommended Actions: Convert and test thoroughly

converted_config.json
├─ Ports (with OTG location format)
├─ Devices (BGP, OSPF, etc.)
├─ Traffic Flows (converted to OTG format)
└─ Assertions (converted where applicable)
```

---

## Supported Protocols

✓ **Routing:**
- BGP (eBGP, iBGP)
- OSPF (v2, v3)
- ISIS
- RIPv2

✓ **Link Layer:**
- LACP / LAG
- LLDP
- VLAN

✓ **Other:**
- IPv4 / IPv6
- Static Routes
- Basic Traffic Flows

---

## Unsupported Features

✗ **Advanced Features:**
- Segment Routing (SR-MPLS) — Workaround: emulate with static routes
- Inline SLA Monitoring — Workaround: use Snappi metrics collection
- Custom Protocol Extensions — May require manual adjustment
- Proprietary IxNetwork Features — No OTG equivalent

---

## Migration Workflow

### Step 1: Check Feasibility
```bash
/migrate-ix
[paste IxNetwork config]
```

Review feasibility report. If < 80% convertible, evaluate workarounds.

### Step 2: Get Converted Config
```bash
# From migration output:
converted_config.json
```

### Step 3: Review Conversion Report
```bash
conversion_report.md
# Check what converted, what didn't
# Review suggested workarounds
```

### Step 4: (Optional) Enhance Config
```bash
/otg-gen
Refine converted config with additional details
```

### Step 5: Generate Test Script
```bash
/snappi-script
converted_config.json at localhost:8443
```

### Step 6: Test & Validate
```bash
python test_migrated.py
```

---

## Feasibility Examples

### Example 1: Simple BGP (90% Convertible)
```
IxNetwork Config:
  - 2 ports
  - BGP (AS 65001/65002)
  - 1000 pps traffic
  - Basic assertions

OTG Conversion:
  ✓ Ports → OTG format
  ✓ BGP → OTG devices
  ✓ Traffic → OTG flows
  ✓ Assertions → OTG assertions

Feasibility: 90% (all major features convert)
```

### Example 2: Multi-Protocol (75% Convertible)
```
IxNetwork Config:
  - 4 ports
  - BGP + OSPF + LACP
  - Custom encapsulation (partly unsupported)
  - Advanced SLA monitoring (unsupported)

OTG Conversion:
  ✓ Ports, BGP, OSPF, LACP
  ◐ Encapsulation (partial support, may need adjustment)
  ✗ SLA monitoring (use Snappi metrics instead)

Feasibility: 75% (core protocols OK, advanced features need work)
```

### Example 3: Complex Lab (60% Convertible)
```
IxNetwork Config:
  - 8 ports, multiple protocols
  - Advanced features: SR-MPLS, segment routing
  - Custom extensions

OTG Conversion:
  ✓ Basic protocols (BGP, OSPF, etc.)
  ✗ SR-MPLS (use workaround: static routes)
  ✗ Custom extensions (manual rewrite needed)

Feasibility: 60% (significant rework required)
Recommendation: Evaluate if migration worth the effort
```

---

## Common Workarounds

| IxNetwork Feature | OTG Support | Workaround |
|------------------|------------|-----------|
| BGP | ✓ Full | Native OTG BGP |
| OSPF | ✓ Full | Native OTG OSPF |
| LACP | ✓ Full | Native OTG LAG |
| SR-MPLS | ✗ None | Static routes + emulation |
| Advanced SLA | ◐ Partial | Use Snappi metrics collection |
| Custom Encap | ◐ Partial | Standard encapsulation only |
| Inline Monitoring | ✗ None | Post-test metrics analysis |

---

## Decision Tree: Should You Migrate?

```
Feasibility >= 90%?
  YES → Migrate! Quick conversion, minimal rework
  NO  → Feasibility 70-90%?
    YES → Migrate with workarounds, some rework needed
    NO  → Feasibility < 70%?
      YES → Evaluate: Cost of migration vs rework
      NO  → Not recommended: Too much manual effort
```

---

## Tips for Successful Migration

1. **Start simple:** Migrate basic test first, then add complexity
2. **Review report:** Read conversion report carefully
3. **Test thoroughly:** Converted config may need tuning
4. **Ask for help:** If feasibility is borderline, consult SE
5. **Keep original:** Don't delete IxNetwork config until validated

---

## After Migration

### Validate Converted Config
```bash
# Review converted_config.json
cat converted_config.json

# Check for obvious issues
# Verify port definitions
# Validate device configs
```

### Test Migrated Setup
```bash
/snappi-script
Use converted_config.json

python test_migrated_bgp.py
# Compare results with original IxNetwork test
```

### Enhance if Needed
```bash
/otg-gen
Refine/enhance migrated config
```

---

## Next Steps

1. **Run migration:** `/kengotg-migrate-ix` with your IxNetwork config
2. **Review report:** Check feasibility and conversions
3. **Generate script:** `/kengotg-snappi-script` to create test
4. **Test:** Run and compare with original
5. **Refine:** Use `/kengotg-otg-gen` to enhance if needed

---

## See Also

- `/kengotg-otg-gen` — Generate/enhance OTG config
- `/kengotg-snappi-script` — Convert to executable test
- `/kengotg-deploy-ixia` — Deploy Ixia-c infrastructure
- `/kengotg-show-skills` — Skill overview
- `/kengotg-examples` — More migration examples
