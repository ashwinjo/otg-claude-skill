# Claude Code Skills - Network Testing Automation

**Available Skills for Network Test Automation**

This directory contains Claude AI skills for IxNetwork and OTG/KENG configuration conversion, generation, and script automation.

---

## Skills Overview

### 1. **ixnetwork-to-keng-converter**

**Purpose:** Convert IxNetwork test configurations to vendor-neutral OTG/KENG format

**When to use:**
- Migrating from IxNetwork to KENG/ixia-c
- Checking if a config can be converted
- Planning multi-tool test strategy

**Capabilities:**
- ✅ Auto-detects RestPy code or JSON input
- ✅ Performs feasibility analysis
- ✅ Generates OTG JSON configuration
- ✅ Produces detailed conversion report

**Supported Features:** BGP, Ethernet, IPv4, VLAN, Traffic flows
**Unsupported:** OSPF, LACP, LLDP, stateful protocols

**Location:** `./ixnetwork-to-keng-converter/`
**Entry Point:** `/ixnetwork-to-keng-converter`

---

### 2. **otg-config-generator**

**Purpose:** Generate OTG configurations from natural language descriptions

**When to use:**
- Creating OTG configs from scratch
- Converting test scenarios to JSON
- Building complex topologies (BGP, LAGs, VLANs)

**Capabilities:**
- ✅ Parses natural language test intent
- ✅ Maps to OTG schema
- ✅ Validates completeness & constraints
- ✅ Outputs production-ready JSON

**Supported Features:** Ports, Devices, BGP, ISIS, LACP, LLDP, VLANs, Traffic, Captures

**Location:** `./otg-config-generator/`
**Entry Point:** `/otg-config-generator`

---

### 3. **snappi-script-generator**

**Purpose:** Generate production-ready Python Snappi test scripts from OTG configs

**When to use:**
- Converting OTG configs to executable tests
- Creating test automation scripts
- Building protocol setup + traffic + metrics collection

**Capabilities:**
- ✅ Generates full Snappi Python scripts
- ✅ Handles protocol setup & timing
- ✅ Implements traffic control & metrics
- ✅ Includes error handling & cleanup

**Supported:** BGP, LACP, LLDP, traffic flows, packet capture, assertions

**Location:** `./snappi-script-generator/`
**Entry Point:** `/snappi-script-generator`

---

## Workflow Example

```
Scenario: "I have an IxNetwork BGP test I want to run on KENG"

Step 1: Convert IxNetwork to OTG
  /ixnetwork-to-keng-converter
  → Input: RestPy code or JSON
  → Output: otg_config.json + conversion_report.md

Step 2 (Optional): Enhance or generate new config
  /otg-config-generator
  → Input: "Add 4 BGP sessions with traffic"
  → Output: Enhanced otg_config.json

Step 3: Generate test script
  /snappi-script-generator
  → Input: otg_config.json + infrastructure.yaml
  → Output: test_bgp.py (executable)

Step 4: Run the test
  python test_bgp.py
  → Configures KENG, starts protocols, runs traffic, collects metrics
```

---

## Quick Start by Skill

### Using ixnetwork-to-keng-converter

```bash
/ixnetwork-to-keng-converter

User: "Convert this IxNetwork BGP config:
from ixnetwork_restpy...
..."

Output: otg_config.json + conversion_report.md
```

### Using otg-config-generator

```bash
/otg-config-generator

User: "Create a BGP test with 2 ports, AS 101 and AS 102, with bidirectional traffic"

Output: Valid OTG JSON configuration
```

### Using snappi-script-generator

```bash
/snappi-script-generator

User: "Generate a Snappi script from this OTG config:
[paste otg_config.json]
Infrastructure: Ixia-c running on 192.168.1.100:8080"

Output: test_script.py (ready to run)
```

---

## Skill Selection Guide

| Task | Skill | Output |
|------|-------|--------|
| **Migrate IxNetwork → OTG** | ixnetwork-to-keng-converter | JSON config + report |
| **Create OTG from description** | otg-config-generator | JSON config |
| **Convert OTG → Snappi script** | snappi-script-generator | Python script |
| **Understand IxNetwork→OTG mapping** | ixnetwork-to-keng-converter | Detailed report |
| **Test multi-tool strategy** | ixnetwork-to-keng-converter | Feasibility analysis |
| **Build protocol topology** | otg-config-generator | OTG JSON |
| **Automate test execution** | snappi-script-generator | Executable test |

---

## Documentation Structure

Each skill folder contains:

```
skill-name/
├── SKILL.md              ← Technical reference
├── README.md             ← User guide
├── PRODUCTION_CHECKLIST.md (if applicable)
└── evals/
    ├── evals.json        ← Test case definitions
    └── files/            ← Test input examples
```

---

## For Organization Members

**Finding the right skill:**
1. Read this INDEX.md
2. Visit the skill's README.md for quick start
3. Check SKILL.md for technical details
4. Review evals/files/ for examples

**Common tasks:**
- "Convert IxNetwork" → `ixnetwork-to-keng-converter`
- "Create OTG config" → `otg-config-generator`
- "Run test on KENG" → `snappi-script-generator`

---

## Support & Troubleshooting

**For each skill:**
- See individual README.md → Troubleshooting FAQ
- Review evals/files/ for examples
- Check SKILL.md for technical details

**For skill ecosystem:**
- This INDEX.md (what you're reading now)

---

## Version & Status

| Skill | Version | Status | Last Updated |
|-------|---------|--------|---|
| ixnetwork-to-keng-converter | 1.0 | ✅ Production-Ready | 2026-03-17 |
| otg-config-generator | 1.0 | ✅ Production-Ready | 2026-03-17 |
| snappi-script-generator | 1.0 | ✅ Production-Ready | 2026-03-17 |

---

**Created:** March 2026
**For:** Network Test Automation
**Status:** All skills are production-ready
