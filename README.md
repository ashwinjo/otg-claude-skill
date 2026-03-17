# KENG OTG Traffic Testing Pipeline

## Quick Start

Your complete traffic testing pipeline with two complementary skills:

### 🎯 Skill #1: otg-config-generator
**Generate OTG configurations from natural language intent**
- Converts test descriptions → vendor-neutral OTG JSON configs
- Supports: BGP, ISIS, LACP, LLDP, VLAN, multiple flows, etc.
- Status: ✅ Ready to use

### 🚀 Skill #2: snappi-script-generator  
**Generate executable Snappi scripts from configs**
- Converts OTG config + infrastructure YAML → standalone Python script
- Handles: API connection, protocol startup, metrics collection, assertions
- Interactive prompts (phase 1) → silent+JSON reports (phase 2)
- Status: ✅ Ready to use

## Files in This Directory

```
kengotg/
├── bgp_keng.json                          Example OTG config (BGP test)
├── infrastructure.yaml                    Example infrastructure spec
├── README.md                              This file
├── SNAPPI_SKILL_SUMMARY.md               Complete workflow guide
├── IXNETWORK_TO_KENG_ANALYSIS.md         IxNetwork conversion analysis
│
└── .claude/skills/
    ├── otg-config-generator/             Skill #1
    └── snappi-script-generator/          Skill #2
```

## Usage Example

### 1. Create Infrastructure YAML
```yaml
# infrastructure.yaml
controller:
  ip: "10.0.0.1"
  port: 8443
  protocol: "https"
ports:
  - name: "P1"
    location: "eth1"
  - name: "P2"
    location: "eth2"
test_config:
  duration_seconds: 60
  metrics_interval_seconds: 5
```

### 2. Generate OTG Config
```
Claude: "Create BGP test with 2 ports, AS 101 and AS 102"
→ otg-config-generator skill
→ bgp_keng.json
```

### 3. Generate Snappi Script
```
Claude: "Generate Snappi script for bgp_keng.json"
→ snappi-script-generator skill
→ test_bgp_keng.py
```

### 4. Run the Test
```bash
pip install snappi
python test_bgp_keng.py
```

## Documentation

- **SNAPPI_SKILL_SUMMARY.md** - Complete workflow guide with examples
- **IXNETWORK_TO_KENG_ANALYSIS.md** - How we converted IxNetwork to KENG
- Skills: Read `SKILL.md` in each skill directory for full details

## Architecture

```
User Intent
    ↓
[otg-config-generator]
    ↓
OTG JSON Config
    ↓ + Infrastructure YAML
[snappi-script-generator]
    ↓
Standalone Python Script
    ↓
python test_xxx.py
    ↓
Test Results + JSON Report
```

## Key Features

✅ Vendor-neutral (works with any OTG-compliant traffic generator)
✅ Standalone scripts (no external dependencies besides snappi)
✅ Production-ready (error handling, retry logic, graceful cleanup)
✅ Configurable assertions (packet loss, session counts, latency, etc.)
✅ Interactive prompts (phase 1) → silent execution (phase 2)
✅ JSON report generation for CI/CD integration

## Next Steps

1. Review `bgp_keng.json` example config
2. Customize `infrastructure.yaml` for your lab
3. Use the skills to generate test scripts
4. Execute and validate

For detailed workflow guide, see: `SNAPPI_SKILL_SUMMARY.md`
