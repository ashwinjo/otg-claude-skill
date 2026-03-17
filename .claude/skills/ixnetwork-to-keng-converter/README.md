# IxNetwork to OTG/KENG Converter Skill

**Convert IxNetwork test configurations to vendor-neutral Open Traffic Generator (OTG/KENG) format.**

A Claude AI skill that automatically detects, analyzes, and converts IxNetwork RestPy code and JSON configurations to production-ready OTG/KENG JSON configurations with detailed conversion reports.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Feature Overview](#feature-overview)
- [Supported/Unsupported Features](#supportedunsupported-features)
- [How to Use (User Guide)](#how-to-use-user-guide)
- [Installation](#installation)
- [Troubleshooting](#troubleshooting)
- [Architecture & Design](#architecture--design)
- [Contributing](#contributing)

---

## Quick Start

### For Claude Code Users

```bash
# Invoke the skill in Claude Code:
/ixnetwork-to-keng-converter
```

Then provide your IxNetwork configuration:

```
Prompt: "Convert this IxNetwork RestPy BGP config to OTG:

from ixnetwork_restpy.testplatform import TestPlatform
tp = TestPlatform('10.36.231.231', rest_port=443, userName='admin', password='admin')
session_assistant = tp.Sessions.add().Ixnetwork

portMap = session_assistant.PortMapAssistant()
portMap.Map('10.36.231.231', CardId=9, PortId=2, Name='Port_1')
...
"
```

**Output:**
```
✅ CONVERSION SUCCESSFUL

otg_config.json       → Ready-to-deploy OTG configuration
conversion_report.md  → Detailed conversion summary
```

---

## Feature Overview

### What This Skill Does

1. **Auto-detects input format:**
   - IxNetwork RestPy Python code
   - IxNetwork JSON configuration files
   - File paths (.py, .ipynb, .json)

2. **Performs feasibility analysis:**
   - Scans for all IxNetwork objects and methods
   - Checks compatibility with OTG MVP
   - Lists unsupported features with severity (blocker vs workaround)

3. **Generates dual output:**
   - **otg_config.json** — Valid OTG configuration ready for deployment
   - **conversion_report.md** — Comprehensive summary including:
     - What converted successfully
     - Workarounds applied
     - Known differences & caveats
     - Step-by-step deployment instructions
     - Comparison with original IxNetwork behavior

---

## Supported/Unsupported Features

### ✅ Fully Supported (MVP)

| Feature | IxNetwork → OTG | Status |
|---------|-----------------|--------|
| **BGP** | BgpIpv4Peer → bgp[] + neighbors[] | ✅ eBGP & iBGP |
| **Ethernet** | Ethernet → device_eth[] | ✅ MAC addressing |
| **IPv4** | Ipv4 → ipv4_addresses[] | ✅ Static addresses |
| **VLAN** | Vlan → vlans[] | ✅ Basic VLAN config |
| **Traffic** | TrafficItem → flows[] | ✅ Bidirectional → 2 flows |
| **Ports** | PortMapAssistant → ports[] | ✅ Port mapping |
| **Topology** | Topology + DeviceGroup → devices[] | ✅ Device hierarchy |

### ⚠️ Partially Supported (Workarounds)

| Feature | Limitation | Workaround |
|---------|-----------|-----------|
| **Multiplier** | Procedural in IxNetwork, not in OTG config | Expanded to explicit devices |
| **Address Increment** | Auto-expansion via multiplier | Single address + runtime expansion |
| **Advanced BGP** | Route filtering, redistribution | Manual post-config |
| **Tracking** | sourceDestEndpointPair granularity | Flow-level statistics only |

### ❌ Unsupported (Blockers)

| Feature | Why Not Supported | Recommendation |
|---------|------------------|-----------------|
| **OSPF, ISIS, RIP** | Not in OTG MVP (BGP only) | Use BGP or stay on IxNetwork |
| **LACP, LLDP** | Not in OTG MVP | Keep test on IxNetwork |
| **Stateful Protocols** | TCP, UDP state tracking not supported | Run on IxNetwork |
| **QoS, Multicast** | Advanced traffic features not in OTG | Keep test on IxNetwork |
| **Deep Packet Inspection** | Application-layer tracking | Not feasible in OTG |

---

## How to Use (User Guide)

### Scenario 1: Convert a BGP Test (RestPy Code)

**Your situation:** You have a working IxNetwork RestPy BGP test and want to migrate to KENG.

**Steps:**

1. **Gather your RestPy code:**
   ```python
   # Copy your Python file or code snippet
   from ixnetwork_restpy.testplatform import TestPlatform
   ...
   ```

2. **Open Claude Code and invoke the skill:**
   ```
   /ixnetwork-to-keng-converter
   ```

3. **Provide the code:**
   ```
   Convert this IxNetwork RestPy BGP configuration:

   [paste your Python code here]
   ```

4. **Review the outputs:**
   - **otg_config.json** — Ready to deploy to ixia-c/KENG
   - **conversion_report.md** — Read through workarounds, warnings, and deployment steps

5. **Fix any issues:**
   - MAC address collisions (skill flags these)
   - Network groups (routes) are optional extensions

6. **Deploy:**
   Follow the "Next Steps" section in the conversion report.

---

### Scenario 2: Convert a JSON Config

**Your situation:** You have an IxNetwork JSON configuration (e.g., `testCaseTgenConfig.json`) and need OTG format.

**Steps:**

1. **Prepare your JSON file.**

2. **Invoke the skill:**
   ```
   /ixnetwork-to-keng-converter
   ```

3. **Provide the JSON:**
   ```
   Convert this IxNetwork JSON configuration:

   {
     "tgenConfig": {
       "endpoint1": { ... },
       "endpoint2": { ... }
     }
   }
   ```

4. **Skill will:**
   - Parse endpoints → ports and devices
   - Extract IPv4 config → ipv4_addresses[]
   - Map BGP parameters → bgp[] + neighbors[]
   - Generate OTG JSON

---

### Scenario 3: Check if Conversion is Possible

**Your situation:** You have a complex IxNetwork test and want to know if it can be converted to OTG without losing features.

**Steps:**

1. **Provide a summary of your config:**
   ```
   I have an IxNetwork test with:
   - 4 ports
   - OSPF routing
   - 200 routes advertised
   - Advanced traffic tracking (sourceDestEndpointPair)
   - QoS marking

   Can this be converted to OTG?
   ```

2. **Skill will:**
   - List supported features ✅
   - List unsupported features ❌
   - Recommend alternatives (split into multiple tests, etc.)
   - Provide a feasibility report

---

### Scenario 4: Plan Multi-Tool Test Strategy

**Your situation:** You want to use both IxNetwork and KENG for different tests.

**Steps:**

1. **List all your tests:**
   ```
   I have these IxNetwork tests:
   1. BGP convergence (2 ports, 100 routes)
   2. OSPF failover (4 ports, 500 routes, advanced tracking)
   3. QoS marking (8 ports, DPI)
   4. BGP with VLANs (2 ports, VLAN tagging)

   Which can I move to KENG?
   ```

2. **Skill will:**
   - Analyze each test
   - Classify as convertible ✅ or not ❌
   - Suggest a migration strategy

**Expected output:**
```
Test 1 (BGP)          → ✅ Convertible to KENG
Test 2 (OSPF)         → ❌ Keep on IxNetwork (OSPF unsupported)
Test 3 (QoS)          → ❌ Keep on IxNetwork (QoS unsupported)
Test 4 (BGP + VLAN)   → ✅ Convertible to KENG

Strategy:
- Move tests 1 & 4 to KENG (saves license cost, vendor-neutral)
- Keep tests 2 & 3 on IxNetwork (advanced features)
```

---

## Installation

### For Claude Code Users

The skill is already installed in your Claude Code environment if:
- You're in the project directory: `/Users/ashwin.joshi/kengotg/`
- The skill folder exists at: `.claude/skills/ixnetwork-to-keng-converter/`

**To verify:**
```bash
ls -la .claude/skills/ixnetwork-to-keng-converter/
```

Expected output:
```
SKILL.md          # Skill documentation
README.md         # This file
evals/            # Test cases (for development/validation)
├── evals.json
└── files/
    ├── eval1_bgp_restpy.py
    ├── eval2_ixnetwork_json.json
    ├── eval3_ospf_restpy.py
    └── eval4_bgp_vlan.py
```

### For Other Claude Environments

If using Claude in a different IDE or environment:
1. Copy the skill folder to your project's `.claude/skills/` directory
2. Restart Claude Code
3. The skill will auto-load

---

## Usage Within Your Organization

### Recommended Workflow

```
Team Member
    ↓
"I have an IxNetwork test"
    ↓
Claude Code Terminal
    ↓
/ixnetwork-to-keng-converter
    ↓
[Paste IxNetwork config]
    ↓
Skill Analysis
├─ Feasibility check
├─ Feature mapping
└─ Generate outputs
    ↓
otg_config.json + conversion_report.md
    ↓
Review Conversion Report
├─ Supported features
├─ Workarounds applied
├─ Warnings & caveats
└─ Deployment steps
    ↓
Deploy to ixia-c/KENG or Keep on IxNetwork
```

### Integration with CI/CD

**Example: Automated conversion in your pipeline**

```python
# Python wrapper script
import subprocess
import json

def convert_ixnetwork_to_otg(config_path):
    """Invoke the skill and capture outputs"""
    result = subprocess.run([
        'claude', 'code',
        '--invoke-skill', 'ixnetwork-to-keng-converter',
        '--input', config_path
    ], capture_output=True)

    # Parse outputs
    otg_config = json.loads(result.stdout['otg_config.json'])
    report = result.stdout['conversion_report.md']

    return otg_config, report

# Use in CI/CD pipeline
config, report = convert_ixnetwork_to_otg('test_config.py')
if 'blockers' not in report:
    deploy_to_keng(config)
else:
    print(f"Cannot convert: {report}")
```

---

## Troubleshooting

### Q: Skill didn't recognize my IxNetwork code

**Check:**
- Is your code valid Python or JSON?
- Does it use IxNetwork RestPy API? (e.g., `BgpIpv4Peer.add()`)
- Are there syntax errors?

**Solution:**
- Paste the exact code snippet (not pseudo-code)
- Include the imports and setup (TestPlatform, SessionAssistant)
- Provide context: "This is a 2-port BGP test"

---

### Q: Conversion says "Not Possible" but I need to migrate

**Check the blockers:**
- OSPF? → Switch to BGP
- Stateful protocols? → Run only data-plane tests
- QoS? → Test basics on KENG, advanced on IxNetwork

**Alternatives:**
1. **Split the test:** Move some scenarios to KENG, some to IxNetwork
2. **Simplify the config:** Remove unsupported features
3. **Stay on IxNetwork:** If all features are critical

---

### Q: MAC addresses are colliding in the output

**Why:** Skill auto-increments based on IxNetwork source; sometimes multiple devices start with the same base.

**Solution:**
- Open `otg_config.json`
- Search for duplicate MACs: `"mac": "00:11:22:33:44:02"`
- Change to unique values: `"mac": "00:11:22:33:44:04"`

---

### Q: My network groups (routes) aren't in the OTG config

**Why:** Network groups are optional in OTG. Skill focuses on core protocol setup.

**Solution:**
- Manual extension: Add to `otg_config.json`:
  ```json
  {
    "network_group": [
      {
        "name": "routes_as101",
        "multiplier": 100,
        "ipv4_prefix_pools": [
          {
            "name": "pool_1",
            "network_address": "10.10.0.1",
            "prefix_length": 32
          }
        ]
      }
    ]
  }
  ```
- Reference in BGP: `"route_ranges": [{"from_network_group": "routes_as101"}]`

---

### Q: Multiplier=2 created 4 devices instead of using a multiplier in OTG

**Why:** OTG config is declarative; multiplier is runtime orchestration. Expanding is clearer.

**Solution:**
- Use the expanded device list as-is (easier to debug)
- Or programmatically expand at test time:
  ```python
  # Pseudo-code
  for i in range(multiplier):
      device = base_device.copy()
      device['name'] = f"device_{i}"
      device['bgp'][0]['router_id'] = increment_ip(base_ip, i)
      config['devices'].append(device)
  ```

---

### Q: Traffic rates differ between IxNetwork and OTG

**Why:** Different traffic engines (IxNetwork vs ixia-c) may have different scheduling.

**Solution:**
1. Run a baseline test on both platforms
2. Capture actual rates
3. Adjust expectations in your assertions
4. Document the variance in your test report

---

## Architecture & Design

### Design Philosophy

1. **Declarative over Procedural:** OTG configs are static definitions, not scripts
2. **Explicit over Implicit:** All devices, addresses, BGP sessions are explicitly listed
3. **Schema-Compliant:** All outputs pass OTG schema validation
4. **Report-Driven:** Always provide detailed reports explaining conversions
5. **Fail-Safe:** If conversion impossible, explain why and suggest alternatives

### How Conversion Works

**Input Analysis Phase:**
- Scans Python/JSON for IxNetwork patterns
- Identifies objects: Topology, DeviceGroup, BgpIpv4Peer, TrafficItem, etc.
- Builds an AST (abstract syntax tree) of the configuration

**Feasibility Check Phase:**
- Maps each IxNetwork concept to OTG equivalent
- Marks as: ✅ Supported | ⚠️ Partial | ❌ Unsupported
- Determines if conversion possible (no blockers)

**Transformation Phase:**
- Expands multipliers into explicit devices
- Flattens hierarchies (DeviceGroup → device)
- Converts parameters (e.g., LocalAs2Bytes → asn)
- Generates OTG JSON

**Reporting Phase:**
- Documents all transformations
- Warns about known differences
- Provides deployment instructions

---

## Contributing

### Want to Improve the Skill?

**Fork/Extend the Skill:**

1. **Add support for new features:**
   - OSPF, LACP, LLDP (extend MVP)
   - Advanced BGP (route filtering, redistribution)

2. **Improve detection:**
   - Handle more IxNetwork API patterns
   - Support .ipynb extraction

3. **Better workarounds:**
   - Generate Python helper scripts for multiplier expansion
   - Auto-generate test runners

**Process:**
1. Update `SKILL.md` with new feature details
2. Add test cases to `evals/files/`
3. Test with `/ixnetwork-to-keng-converter`
4. Create a pull request with improvements

---

## Support & Contact

**Questions?**
- Review the `SKILL.md` file for technical details
- Check the `conversion_report.md` generated for your specific config
- Review test cases in `evals/files/` for examples

**Feedback?**
- File an issue in your project repo
- Include the IxNetwork config you tried to convert
- Include the skill output and what went wrong

---

## License & Attribution

- **Source:** Converted from analysis document: `IXNETWORK_TO_KENG_ANALYSIS.md`
- **Reference Config:** `bgp_keng.json` (example 2-port BGP test)
- **Org:** Your Organization
- **Created:** March 2026
- **Status:** Production-Ready

---

## Appendix: Example Conversions

### Example 1: Simple BGP (Convertible ✅)

**Input:** 2 ports, BGP AS 101 ↔ AS 102, bidirectional traffic

**Output:**
```
otg_config.json (4 KB)
├─ 2 ports
├─ 2 devices
├─ 2 BGP instances
└─ 2 flows

conversion_report.md
├─ ✅ All features supported
├─ ⚠️ Multiplier expanded (note for user)
└─ 📋 Ready to deploy
```

### Example 2: OSPF Config (Not Convertible ❌)

**Input:** OSPF routing protocol

**Output:**
```
conversion_report.md
├─ ❌ OSPF not supported in OTG MVP
├─ Recommendation: Use BGP or stay on IxNetwork
└─ No otg_config.json generated
```

### Example 3: BGP with VLANs (Convertible ✅)

**Input:** BGP peering within VLANs

**Output:**
```
otg_config.json
├─ devices[]
│  └─ vlans[]
│     └─ ipv4_addresses[] (within VLAN context)
└─ bgp[] (VLAN-aware peering)

conversion_report.md
├─ ✅ VLANs supported
├─ ✅ BGP within VLANs converted
└─ Ready to deploy
```

---

**Version:** 1.0
**Last Updated:** March 17, 2026
**Status:** Production-Ready ✅
