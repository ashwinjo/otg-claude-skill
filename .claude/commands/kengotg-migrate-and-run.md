---
name: kengotg-migrate-and-run
description: IxNetwork migration and execution workflow
disable-model-invocation: false
allowed-tools: []
---

# Migrate-And-Run — IxNetwork Migration + Execution

Complete workflow: migrate IxNetwork config to OTG, generate test script, deploy infrastructure, and run.

## Quick Start

Migrate and execute IxNetwork test:

```
/kengotg-migrate-and-run
[paste IxNetwork RestPy code or JSON]
```

Get conversion report, OTG config, infrastructure, executable script, and test results.

---

## Workflow Overview

```
Step 1: Analyze & Convert
├─ Check IxNetwork config
├─ Assess feasibility (0-100%)
├─ List supported/unsupported features
└─ Generate OTG config

       ↓

Step 2: Deploy Infrastructure
├─ Determine deployment method
├─ Generate Docker Compose manifest
├─ Deploy to Docker
└─ Validate health

       ↓

Step 3: Generate Test Script
├─ Embed OTG config in Python
├─ Implement protocol setup
├─ Add metrics & assertions
└─ Validate syntax

       ↓

Step 4: Execute Test
├─ Start infrastructure
├─ Run test script
├─ Collect results
└─ Generate JSON report

       ↓

Complete: Results Ready!
```

---

## Input: IxNetwork Configuration

### Python RestPy Code
```python
ixnObj = IxNetwork()
ixnObj.connect('10.1.1.1', 443, 'admin', 'admin')
vport1 = ixnObj.Vport.add()
bgp1 = vport1.Protocols.Bgp.add()
bgp1.RouterId = '1.1.1.1'
bgp1.AsNumber = 65001
# ... more configuration
```

### IxNetwork JSON Config
```json
{
  "vports": [...],
  "protocols": [...],
  "traffic": [...]
}
```

### Description
```
BGP test with 2 ports, AS 65001 and AS 65002,
bidirectional traffic, measure convergence
```

---

## Workflow Steps

### Step 1: Paste IxNetwork Config
```
/kengotg-migrate-and-run
[your IxNetwork config]
```

**Outputs:**
- Feasibility report (e.g., 85% convertible)
- Supported features ✓
- Unsupported features ✗
- Suggested workarounds
- Converted OTG config JSON

### Step 2: Review Conversion Report
```
Feasibility: 85%
Status: Proceed with migration

Supported (85%):
✓ 2 ports
✓ BGP protocol
✓ Traffic flows
✓ Basic assertions

Unsupported (15%):
✗ Advanced SLA monitoring
  Workaround: Use Snappi metrics collection
```

### Step 3: Deploy & Generate Script
Command automatically:
- Deploys Ixia-c with Docker Compose
- Injects port mapping into OTG config
- Generates Snappi test script
- Validates all components

### Step 4: Execute Test
```bash
# Automated execution:
# 1. Docker containers start
# 2. Controller health verified
# 3. Test script runs
# 4. Results collected
# 5. JSON report generated
```

---

## Example Scenarios

### Simple BGP Migration
```
IxNetwork config:
- 2 ports
- BGP (AS 65001/65002)
- 1000 pps traffic

Result:
✓ 95% convertible
✓ All features supported
✓ Full deployment + execution
```

### Multi-Protocol Migration
```
IxNetwork config:
- 4 ports
- BGP + OSPF + LACP
- Complex encapsulation

Result:
◐ 75% convertible
◐ Core features supported
◐ Some workarounds needed
→ Deployment + execution with manual adjustments
```

### High-Complexity Setup
```
IxNetwork config:
- 8 ports
- BGP + OSPF + ISIS + SLA monitoring
- Custom encapsulation

Result:
✗ 50% convertible
✗ Multiple blockers
→ Not recommended for automated migration
→ Manual conversion suggested
```

---

## What You Get

### Conversion Outputs
✓ `conversion-report.md` — Feasibility analysis + workarounds
✓ `converted_config.json` — OTG JSON config
✓ `feature-mapping.md` — IxNetwork → OTG mapping table

### Deployment Outputs
✓ `docker-compose-migrated.yml` — Infrastructure
✓ `setup-ixia-c-migrated.sh` — Deployment script
✓ `port-mapping.json` — Port locations

### Script Outputs
✓ `test_migrated.py` — Executable test script
✓ `execution-guide.md` — How to run

### Results
✓ `test_results_*.json` — Metrics, assertions, report

---

## Execution

### Automated (Recommended)
```
/kengotg-migrate-and-run
[paste IxNetwork config]

# All steps execute automatically:
# 1. Convert
# 2. Deploy
# 3. Generate
# 4. Execute
# 5. Report
```

### Manual (Step-by-Step)
```bash
# 1. Deploy infrastructure
docker-compose -f docker-compose-migrated.yml up -d

# 2. Wait for health check
sleep 10

# 3. Execute test
python test_migrated.py

# 4. Review results
cat test_results_*.json
```

---

## Feasibility Matrix

| Feasibility | Status | Action |
|------------|--------|--------|
| 90-100% | ✓ GOOD | Proceed with automated migration |
| 75-89% | ◐ FAIR | Proceed with minor adjustments |
| 60-74% | ⚠️ RISKY | Manual review recommended |
| <60% | ✗ BLOCKED | Manual conversion suggested |

---

## Handling Unsupported Features

### Unsupported: Advanced SLA Monitoring
**Workaround:** Use Snappi metrics collection
```python
# In generated script
results = api.get_results()
metrics = {
    'throughput_pps': results['traffic']['pps'],
    'latency_ms': results['traffic']['latency'],
    'packet_loss': results['traffic']['loss_pct']
}
```

### Unsupported: SR-MPLS
**Workaround:** Emulate with static routes
```python
# Add static routes in OTG config
static_routes = [{
    'prefix': '2.2.2.0/24',
    'next_hop': '1.1.1.2'
}]
```

### Unsupported: Custom Encapsulation
**Workaround:** Use standard encapsulation
```json
{
  "encapsulation": "ethernet",
  "vlan": {
    "id": 100,
    "priority": 5
  }
}
```

---

## Troubleshooting

**Conversion fails:**
- Check IxNetwork config format (Python or JSON)
- Verify basic syntax
- Simplify config if complex

**Deployment fails:**
- Check Docker running: `docker ps`
- Check disk space: `docker system df`
- Check port availability

**Script errors:**
- Verify Python 3.8+: `python --version`
- Install Snappi: `pip install snappi`
- Check controller URL

**Results unexpected:**
- Review conversion report
- Check port alignment
- Verify test parameters
- Inspect JSON report for details

---

## Comparison: Before vs After

### Before (IxNetwork)
```
- IxNetwork license required
- Proprietary format
- Limited portability
- GUI-based configuration
```

### After (KENG/OTG)
```
✓ No IxNetwork license needed
✓ Standards-based (OpenAPI)
✓ Portable (any OTG platform)
✓ Code/config-based
✓ CI/CD friendly
✓ Containerized (Ixia-c)
```

---

## Success Criteria

✓ **Conversion:** Feasibility >= 75%
✓ **Deployment:** Infrastructure healthy
✓ **Script:** Syntax valid, imports correct
✓ **Execution:** Test completes, report generated
✓ **Results:** Assertions pass, metrics meaningful

---

## Next Steps

1. **Migrate:** Paste IxNetwork config
2. **Review:** Check conversion report
3. **Deploy:** Verify infrastructure
4. **Execute:** Run test script
5. **Analyze:** Review JSON results
6. **Iterate:** Refine config/assertions as needed

---

## Tips

- **Start simple:** Migrate basic configs first
- **Preserve originals:** Keep IxNetwork config for reference
- **Test incrementally:** Verify each component works
- **Document:** Annotate workarounds and customizations
- **Version control:** Commit converted configs and scripts

---

## When to Use This Workflow

✓ Migrating from IxNetwork
✓ Evaluating KENG as replacement
✓ One-time migration + validation
✓ Config conversion + immediate execution

---

## When to Use Separate Commands

→ `/kengotg-migrate-ix` if you need:
- Conversion only (no deployment/execution)
- Feasibility analysis before deciding

→ `/kengotg-create-test` if you need:
- Custom test creation (not migration)
- Full control over parameters

---

## Related Commands

- `/kengotg-migrate-ix` — Migration only (conversion + report)
- `/kengotg-create-test` — Full test creation pipeline
- `/kengotg-quick-bgp-test` — Quick BGP shortcut
- `/kengotg-check-licensing` — Licensing evaluation

See `/kengotg-examples` for more migration scenarios.
