---
name: kengotg-otg-gen
description: Quick OTG config generation from natural language
disable-model-invocation: false
allowed-tools: []
---

# OTG-Gen — Quick Config Generation

Rapidly generate Open Traffic Generator configurations from plain English descriptions.

## Quick Start

Describe your test scenario in natural language:

```
/otg-gen
Create a BGP test with 2 ports, AS 65001 and AS 65002, bidirectional 1000 pps traffic
```

The command will generate a production-ready `otg_config.json` file.

---

## Usage Patterns

### Simple BGP Test
```
Create BGP convergence test:
- 2 ports
- AS 65001 and AS 65002
- 1000 pps bidirectional traffic
- 120 second duration
- Assert: BGP converges within 30 seconds
```

### OSPF Failover
```
Create OSPF failover test:
- 4 ports in 2 LAGs
- OSPF Area 0 and Area 1
- Traffic rerouting on failover
- Measure convergence time
```

### Multi-Protocol
```
Create multi-protocol test:
- BGP on ports 1-2 (AS 65001/65002)
- OSPF on ports 3-4 (Area 0/1)
- Cross-protocol traffic
- 60 second duration
```

### LACP Testing
```
Create LAG failover test:
- 4 ports in 2 LAGs (LAG1: ports 1-2, LAG2: ports 3-4)
- Simulate LAG1 failure
- Measure traffic recovery time
- Assert zero packet loss during failover
```

---

## What You Get

✓ `otg_config.json` — Standards-compliant OTG configuration
✓ `otg_config_summary.md` — Human-readable summary
✓ `port_alignment_report.md` — Port mapping verification

---

## Next Steps

1. Review the generated `otg_config.json`
2. Use `/kengotg-snappi-script` to convert to executable Python
3. Deploy infrastructure with `/kengotg-deploy-ixia` if needed
4. Run the test

---

## Tips

- **Be specific:** Include port count, protocol, traffic details
- **Mention time:** Specify test duration and convergence expectations
- **Add assertions:** Tell us what success looks like
- **Reference infrastructure:** If you have existing Ixia-c, mention the controller URL

Example:
```
Create BGP test for Ixia-c at localhost:8443:
- 2 ports (existing infrastructure)
- AS 65001 vs 65002
- 1000 pps bidirectional
- Assert BGP UP within 30 seconds
```

---

## See Also

- `/kengotg-show-skills` — Skill overview
- `/kengotg-snappi-script` — Convert config to executable script
- `/kengotg-deploy-ixia` — Deploy infrastructure first
- `/kengotg-examples` — More workflow examples
