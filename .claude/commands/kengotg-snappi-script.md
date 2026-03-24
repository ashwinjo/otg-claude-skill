---
name: kengotg-snappi-script
description: Quick Snappi test script generation (dispatches to snappi-script-generator-agent)
disable-model-invocation: false
allowed-tools: []
---

# Snappi-Script — Quick Script Generation

Rapidly convert OTG configurations into executable, standalone Python Snappi test scripts.

## Agent Dispatch (REQUIRED)

**This command MUST dispatch to the `snappi-script-generator-agent` subagent.**

Do NOT execute the skill directly. Instead, use the Agent tool:

```
Agent tool call:
  subagent_type: snappi-script-generator-agent
  prompt: <forward the user's script generation request and any arguments>
  description: "Generate Snappi test script"
```

The agent will invoke the `snappi-script-generator` skill internally, handle all generation steps, and return results.

**Hierarchy:** `/kengotg-snappi-script` (command) → `snappi-script-generator-agent` (agent) → `snappi-script-generator` (skill)

---

## Quick Start

Generate a test script from your OTG config:

```
/snappi-script
otg_config.json with controller at localhost:8443
```

You get an immediately executable `test_xxx.py` file.

---

## Usage Patterns

### From OTG Config File
```
/snappi-script
Use otg_config.json (from /otg-gen or deployment)
```

Outputs: `test_bgp_convergence.py` (standalone, executable)

### Specify Controller URL
```
/snappi-script
OTG config: bgp_config.json
Controller: my-ixia-c.internal:8443
```

### With Custom Settings
```
/snappi-script
Config: otg_config.json
Controller: localhost:8443
Test timeout: 300 seconds
Report format: JSON with detailed metrics
```

---

## What You Get

✓ `test_xxx.py` — Fully functional Python script (600+ lines)
✓ `execution_guide.md` — How to run, expected output
✓ All OTG config embedded (no external files needed)
✓ Error handling and retry logic
✓ Metrics collection and JSON reporting

---

## Script Features

**Built-in:**
- Snappi SDK integration
- Connection retry logic (3 attempts, exponential backoff)
- OTG config embedded inline
- Protocol state polling (BGP, OSPF, etc.)
- Traffic start/stop control
- Metrics collection (throughput, latency, packet loss)
- Assertion validation
- JSON report generation
- Full error handling
- Graceful resource cleanup

**Run immediately:**
```bash
python test_bgp_convergence.py
```

No setup, no config files, just run.

---

## Execution Steps

1. **Setup infrastructure** (if needed):
   ```bash
   /deploy-ixia
   ```

2. **Generate OTG config**:
   ```bash
   /otg-gen
   Create BGP test: 2 ports, AS 65001/65002, 1000 pps
   ```

3. **Generate test script**:
   ```bash
   /snappi-script
   otg_config.json at localhost:8443
   ```

4. **Run test**:
   ```bash
   python test_bgp_convergence.py
   ```

5. **Check results**:
   - View JSON report: `test_results_*.json`
   - Review metrics and assertions
   - Troubleshoot if needed

---

## Output Report Example

```json
{
  "test_name": "bgp_convergence",
  "duration": 120,
  "controller": "localhost:8443",
  "status": "PASS",
  "metrics": {
    "traffic": {
      "throughput_pps": 1000,
      "packet_loss": 0,
      "latency_ms": [0.5, 1.2, 0.8]
    },
    "bgp": {
      "convergence_time_seconds": 15,
      "adjacencies_up": 2,
      "routes_learned": 100
    }
  },
  "assertions": [
    {"name": "BGP_convergence_30s", "result": "PASS"},
    {"name": "Zero_packet_loss", "result": "PASS"},
    {"name": "Throughput_1000pps", "result": "PASS"}
  ]
}
```

---

## Common Customizations

**Longer test duration:**
```python
# In generated script
test_duration = 300  # seconds (default: 120)
```

**Different metrics:**
```python
# Add custom metric collection
results = api.get_results(query='port.statistics')
```

**Custom assertions:**
```python
# Modify assertion logic
assert bgp_convergence_time < 20  # seconds
```

---

## Tips

- **Infrastructure first:** Deploy with `/kengotg-deploy-ixia` before generating scripts
- **Config validation:** Review OTG config before script generation
- **Test locally:** Always run scripts locally first before CI/CD
- **Save reports:** JSON reports are auto-saved with timestamps

---

## Troubleshooting

**Connection timeout:**
```
✓ Check controller URL is correct
✓ Verify controller is running: curl -k https://localhost:8443/config
✓ Check firewall/network connectivity
```

**Script won't run:**
```
✓ Verify Python version (3.8+)
✓ Install Snappi: pip install snappi
✓ Check script syntax: python -m py_compile test_xxx.py
```

**Assertions failing:**
```
✓ Review expected vs actual metrics in JSON report
✓ Check timeout values (BGP: 30s, OSPF: 60s)
✓ Verify infrastructure is healthy
```

---

## See Also

- `/kengotg-otg-gen` — Generate OTG config first
- `/kengotg-deploy-ixia` — Deploy infrastructure
- `/kengotg-show-skills` — Skill overview
- `/kengotg-examples` — More workflow examples
