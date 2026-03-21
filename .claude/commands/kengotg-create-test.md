---
name: kengotg-create-test
description: Full test creation pipeline (deploy → config → script)
disable-model-invocation: false
allowed-tools: []
---

# Create-Test — Full Test Creation Pipeline

Complete end-to-end workflow: deploy infrastructure, create OTG config, generate executable test script.

## Quick Start

Create a complete test from scratch:

```
/kengotg-create-test
I need a BGP convergence test with 2 ports, AS 65001 and 65002,
bidirectional 1000 pps traffic, measure convergence time
```

You get everything: deployed infrastructure, OTG config, executable test script.

---

## Workflow Overview

```
Step 1: Deploy Infrastructure
├─ Analyze requirements
├─ Choose Docker Compose or Containerlab
├─ Generate manifests
├─ Deploy and validate
└─ Return port mappings

       ↓

Step 2: Generate OTG Configuration
├─ Parse test intent
├─ Inject port mappings
├─ Generate OTG config
└─ Validate against schema

       ↓

Step 3: Generate Test Script
├─ Convert OTG to Python
├─ Implement protocol setup
├─ Add metrics & assertions
└─ Generate standalone script

       ↓

Complete: Ready to Run!
python test_xxx.py
```

---

## Input Requirements

Describe your test scenario with:

### Required:
- **Test type:** BGP, OSPF, LACP, LLDP, etc.
- **Port count:** How many ports? (e.g., 2, 4, 8)
- **Test description:** What should the test do?

### Optional but Recommended:
- **Duration:** How long should test run? (default: 120s)
- **Traffic rate:** Packets per second? (default: 1000 pps)
- **Assertions:** What defines success? (convergence time, zero loss, etc.)
- **Deployment method:** Docker Compose (simple) or Containerlab (complex)

---

## Example Workflows

### BGP Convergence Test
```
/kengotg-create-test

Test: BGP convergence
Ports: 2
AS Numbers: 65001 and 65002
Traffic: 1000 pps bidirectional
Duration: 120 seconds
Assert: BGP converges within 30 seconds

Deployment: Docker Compose (simple single-host setup)
```

**Output:**
- docker-compose-bgp-cpdp.yml (infrastructure)
- setup-ixia-c-bgp.sh (deployment script)
- bgp_convergence_cpdp.json (OTG config)
- test_bgp_convergence.py (executable test)

### LACP Failover Test
```
/kengotg-create-test

Test: LACP failover simulation
Ports: 4 (2 LAGs, 2 ports each)
LAG1: Ports 1-2, LAG2: Ports 3-4
Failover: Simulate LAG1 failure
Traffic: Reroute to LAG2
Assert: Recovery within 5 seconds, zero loss

Deployment: Docker Compose
```

### Multi-Protocol Complex Test
```
/kengotg-create-test

Test: BGP + OSPF + LACP interaction
Ports: 4
BGP on LAG1 (AS 65001/65002)
OSPF on LAG2 (Area 0/1)
Failover: Drop LAG1, measure convergence
Assert: All protocols converge within 30s

Deployment: Docker Compose
```

---

## What You Get

### Deployment Outputs
✓ `docker-compose-xxx.yml` — Infrastructure manifest
✓ `setup-ixia-c-xxx.sh` — Deployment automation script
✓ `port-mapping.json` — Port location mapping
✓ `deployment-guide.md` — Step-by-step instructions

### Configuration Output
✓ `otg_config.json` — Standards-compliant OTG config
✓ `config-summary.md` — Human-readable summary
✓ `port-alignment-report.md` — Port mapping verification

### Script Output
✓ `test_xxx.py` — Executable Python Snappi script (600+ lines)
✓ `execution-guide.md` — How to run, expected output, troubleshooting
✓ All infrastructure details embedded (no external files needed)

---

## Execution Steps

### 1. Deploy Infrastructure
```bash
# Navigate to generated directory
cd test_bgp_convergence_workspace

# Deploy with Docker Compose
docker-compose -f docker-compose-bgp-cpdp.yml up -d

# Or run automated script
bash setup-ixia-c-bgp.sh
```

### 2. Verify Deployment
```bash
# Check controller
curl -k https://localhost:8443/config

# List running containers
docker ps | grep ixia

# Verify port connectivity
docker exec ixia-c-traffic-engine-a ip link show
```

### 3. Run Test
```bash
# Execute test script
python test_bgp_convergence.py

# Monitor output (real-time progress)
# Watch for: protocol setup, traffic start, convergence detection, results
```

### 4. Review Results
```bash
# JSON report auto-generated
cat test_results_*.json

# Key metrics:
# - BGP convergence time (seconds)
# - Traffic throughput (pps)
# - Packet loss (%)
# - Assertion results (pass/fail)
```

---

## Output Directory Structure

```
test_bgp_convergence_workspace/
├── Infrastructure/
│   ├── docker-compose-bgp-cpdp.yml
│   ├── setup-ixia-c-bgp.sh
│   ├── port-mapping.json
│   └── deployment-guide.md
│
├── Configuration/
│   ├── bgp_convergence_cpdp.json
│   ├── config-summary.md
│   └── port-alignment-report.md
│
├── Script/
│   ├── test_bgp_convergence.py  (executable)
│   └── execution-guide.md
│
└── Results/ (after execution)
    └── test_results_*.json
```

---

## Customization

### Longer Duration
```python
# In generated script
test_duration = 300  # seconds (default: 120)
```

### Different Traffic Rate
```python
# In generated script or OTG config
traffic_rate = 5000  # pps (default: 1000)
```

### Additional Assertions
```python
# Add custom assertions in script
assert bgp_routes_learned >= 100, "Route learning failed"
assert latency_max < 10, "Latency too high"
```

### Change Controller URL
```python
# In generated script
controller_url = "my-ixia-c.internal:8443"
```

---

## Troubleshooting

**Deployment fails:**
- Check Docker daemon running: `docker ps`
- Check disk space: `docker system df`
- Review deployment guide for port conflicts

**Script won't run:**
- Install Snappi: `pip install snappi`
- Verify Python 3.8+: `python --version`
- Check syntax: `python -m py_compile test_xxx.py`

**Assertions fail:**
- Review test results JSON
- Check infrastructure health
- Increase timeouts if needed
- Review assertion logic

**Port alignment issues:**
- Verify port mapping in deployment output
- Check OTG config port definitions
- Ensure script uses correct controller URL

---

## Next Steps

1. **Review outputs:** Examine generated infrastructure, config, and script
2. **Deploy:** Run docker-compose or setup script
3. **Verify:** Check controller health and port connectivity
4. **Execute:** Run the Python test script
5. **Analyze:** Review JSON report and metrics
6. **Iterate:** Customize assertions, parameters, or test scenario

---

## Tips

- **Test incrementally:** Start with simple 2-port test, expand to 4+ ports
- **Save workflows:** Keep successful test configs for reuse
- **Version control:** Commit generated configs and scripts
- **Document:** Annotate custom assertions and modifications
- **Monitor:** Use JSON reports for trend analysis and performance tracking

---

## Related Commands

- `/kengotg-quick-bgp-test` — BGP test shortcut (simplified)
- `/kengotg-migrate-and-run` — IxNetwork migration + execution
- `/kengotg-check-licensing` — Licensing evaluation
- `/kengotg-otg-gen` — Quick config generation (config only)
- `/kengotg-snappi-script` — Quick script generation (script only)
- `/kengotg-deploy-ixia` — Infrastructure only
- `/kengotg-licensing` — Licensing check

See `/kengotg-examples` for more workflow patterns.
