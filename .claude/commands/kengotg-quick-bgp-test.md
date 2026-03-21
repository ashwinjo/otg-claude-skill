---
name: kengotg-quick-bgp-test
description: Quick BGP convergence test shortcut
disable-model-invocation: false
allowed-tools: []
---

# Quick-BGP-Test — BGP Test Shortcut

Rapid BGP convergence test: sensible defaults for quick setup and execution.

## Quick Start

Create a BGP test with defaults:

```
/kengotg-quick-bgp-test
2 ports, AS 65001/65002
```

Or customize:

```
/kengotg-quick-bgp-test
4 ports, AS 65001/65002/65003/65004, 5000 pps, 60 second duration
```

---

## Default Settings

If you don't specify parameters, we use:

```
Ports:           2
AS Numbers:      65001, 65002
Traffic Rate:    1000 pps bidirectional
Duration:        120 seconds
Convergence SLA: 30 seconds
Packet Loss SLA: 0%
Deployment:      Docker Compose
```

---

## Quick Examples

### Minimal (Uses All Defaults)
```
/kengotg-quick-bgp-test
2 ports
```

**Result:** Full BGP test with all defaults applied

### Single Parameter Change
```
/kengotg-quick-bgp-test
4 ports, defaults for everything else
```

**Result:** 4-port BGP test, other parameters default

### Multiple Parameters
```
/kengotg-quick-bgp-test
4 ports, 3000 pps, 60 second duration
```

**Result:** 4-port BGP, 3000 pps, 60s duration, other defaults

### Full Specification
```
/kengotg-quick-bgp-test
4 ports (AS 65001/65002/65003/65004)
Traffic: 2000 pps bidirectional
Duration: 180 seconds
Convergence SLA: 45 seconds
Deployment: Docker Compose
```

---

## Workflow

```
1. Parse parameters (or apply defaults)
2. Deploy Ixia-c with Docker Compose
3. Generate BGP OTG config (with port mapping)
4. Generate Snappi test script
5. Output: Ready-to-run environment
```

---

## What You Get

Same outputs as `/kengotg-create-test`:

✓ `docker-compose-bgp-quick.yml` (infrastructure)
✓ `setup-ixia-c-bgp-quick.sh` (deployment script)
✓ `bgp_quick_config.json` (OTG config)
✓ `test_bgp_quick.py` (executable test)
✓ Execution guides and deployment instructions

---

## Run the Test

```bash
# 1. Deploy
docker-compose -f docker-compose-bgp-quick.yml up -d

# 2. Execute
python test_bgp_quick.py

# 3. Review results
cat test_results_*.json
```

---

## Parameter Reference

### Ports
```
Syntax: N ports (where N = 2, 4, 6, 8, etc.)
Default: 2
Example: /kengotg-quick-bgp-test 4 ports
```

### AS Numbers
```
Auto-generated from port count
2 ports: 65001, 65002
4 ports: 65001, 65002, 65003, 65004
Or specify: AS 65001/65002/65003/65004
```

### Traffic Rate
```
Syntax: N pps (packets per second)
Default: 1000
Example: /kengotg-quick-bgp-test 3000 pps
```

### Duration
```
Syntax: N seconds (test runtime)
Default: 120
Example: /kengotg-quick-bgp-test 60 second duration
```

### Convergence SLA
```
Syntax: N seconds (BGP convergence timeout)
Default: 30
Example: /kengotg-quick-bgp-test 45 second convergence SLA
```

---

## Typical Scenarios

### Quick POC (2 min)
```
/kengotg-quick-bgp-test
2 ports, 1000 pps, 120 second duration
```

### Extended Test (5 min)
```
/kengotg-quick-bgp-test
2 ports, 1000 pps, 300 second duration
```

### High-Scale Test (8 min)
```
/kengotg-quick-bgp-test
8 ports, 5000 pps, 480 second duration
```

### Stress Test (full capacity)
```
/kengotg-quick-bgp-test
4 ports, 10000 pps, 120 second duration
```

---

## Common Customizations

### Increase Port Count
```
/kengotg-quick-bgp-test
8 ports
```
Auto-generates 8 BGP peers (AS 65001-65008)

### Higher Traffic Rate
```
/kengotg-quick-bgp-test
4 ports, 5000 pps
```
Tests at higher throughput

### Longer Duration
```
/kengotg-quick-bgp-test
2 ports, 300 second duration
```
Captures longer convergence patterns

### Stricter SLA
```
/kengotg-quick-bgp-test
2 ports, 20 second convergence SLA
```
Verifies fast convergence

---

## Output Example

```
BGP Convergence Test Results
============================
Ports: 2
AS: 65001, 65002
Traffic: 1000 pps
Duration: 120 seconds

Convergence Time: 15 seconds ✓ (SLA: 30s)
Packet Loss: 0% ✓ (SLA: 0%)
Routes Learned: 200 ✓
Throughput: 1000 pps ✓

Status: PASS
```

---

## Troubleshooting

**Convergence too slow:**
- Increase convergence SLA timeout
- Check network links
- Verify controller health

**Packet loss:**
- Reduce traffic rate
- Check port capacity
- Review infrastructure health

**Script errors:**
- Verify Docker running
- Check Snappi installed: `pip install snappi`
- Review execution guide

---

## When to Use

✓ BGP testing (any scale)
✓ Convergence measurement
✓ Protocol stability validation
✓ Quick baseline tests
✓ Development/demo scenarios

---

## When to Use Full Pipeline Instead

→ `/kengotg-create-test` if you need:
- Multi-protocol testing (BGP + OSPF, etc.)
- Custom test scenarios
- Specific port configurations
- Advanced assertions

---

## Related Commands

- `/kengotg-create-test` — Full pipeline (any protocol)
- `/kengotg-migrate-and-run` — IxNetwork migration
- `/kengotg-check-licensing` — Licensing evaluation
- `/kengotg-examples` — More workflow patterns

---

## Tips

- **Record results:** Save JSON reports for comparison
- **Iterate:** Try different port counts and traffic rates
- **Baseline:** Create baseline test for regression detection
- **Automate:** Integrate with CI/CD pipeline

See `/kengotg-examples` for advanced BGP scenarios.
