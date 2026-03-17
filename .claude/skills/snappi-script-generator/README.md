# Snappi Script Generator Skill

**Generate standalone, production-ready Python Snappi scripts from OTG configurations and infrastructure specifications.**

A Claude AI skill that converts Open Traffic Generator (OTG) JSON configurations into executable Python test scripts with protocol setup, traffic control, metrics collection, and assertions.

---

## Table of Contents

- [Quick Start](#quick-start)
- [What This Skill Does](#what-this-skill-does)
- [Key Capabilities](#key-capabilities)
- [Supported Assertion Types](#supported-assertion-types)
- [How to Use](#how-to-use)
- [Common Patterns](#common-patterns)
- [Output Examples](#output-examples)
- [Reference Documentation](#reference-documentation)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### For Claude Code Users

```bash
# Invoke the skill in Claude Code:
/snappi-script-generator
```

Then provide your OTG configuration and infrastructure details:

```
Prompt: "Generate a Snappi test script from bgp_config.json
Infrastructure YAML:
controller:
  ip: localhost
  port: 8443
  protocol: https

ports:
  - name: P1
    location: 1/1
  - name: P2
    location: 1/2

test_config:
  duration_seconds: 60
  metrics_interval_seconds: 5

Assertions:
- BGP sessions: 2 (equals)
- Packet loss: < 0.01%
- TX frames on flow_p1_to_p2: > 100000
"
```

**Output:**
```
✅ SCRIPT GENERATED SUCCESSFULLY

test_bgp_keng.py       → Standalone executable script
infrastructure.yaml    → Configuration (embedded in script)

Run:
  pip install snappi
  python test_bgp_keng.py
```

---

## What This Skill Does

Converts OTG/KENG JSON configurations into **fully functional, standalone Python scripts** that:

- ✅ Connect to OTG-compliant traffic generators (Ixia-c, KENG, etc.)
- ✅ Load and validate OTG configurations
- ✅ Start all protocols (BGP, ISIS, LACP, LLDP)
- ✅ Manage traffic flows with precise control
- ✅ Collect real-time metrics (port, flow, device-level)
- ✅ Validate test assertions (convergence, packet loss, frame counts)
- ✅ Handle errors with exponential backoff retry
- ✅ Gracefully clean up resources

**Script is portable:** Embeds configuration → no external dependencies except `snappi`.

---

## Key Capabilities

### Protocol Setup
- ✅ BGP (IPv4 & IPv6, IBGP/EBGP, route aggregation, communities)
- ✅ ISIS (L1/L2 adjacencies, multi-device topologies)
- ✅ LACP (LAG configuration, port aggregation)
- ✅ LLDP (device discovery)
- ✅ VLAN (tagged traffic, QinQ)
- ✅ Multi-protocol convergence (composite wait)

### Traffic Control
- ✅ Multiple rate modes: `pps`, `percentage`, `bps`, `fixed_packets`, `fixed_seconds`
- ✅ Bidirectional flows
- ✅ Packet header configuration (Ethernet, VLAN, IPv4, IPv6, TCP, UDP)
- ✅ Flow-level metrics with latency tracking

### Assertions & Validation
- ✅ Protocol convergence (BGP sessions, ISIS adjacencies)
- ✅ Packet loss validation
- ✅ Frame count assertions (TX/RX per flow or port)
- ✅ Port link status checks
- ✅ Latency bounds (average, min, max)
- ✅ BGP route count validation
- ✅ Composite multi-protocol assertions

### Execution Modes
- ✅ Interactive prompts (user control between steps)
- ✅ Silent execution (CI/CD-friendly)
- ✅ JSON report output (machine-parseable results)
- ✅ Graceful error handling with detailed messages

---

## Supported Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `bgp_sessions` | Number of BGP sessions up | `{ "type": "bgp_sessions", "expected_value": 2, "operator": "equals" }` |
| `isis_sessions` | Number of ISIS adjacencies | `{ "type": "isis_sessions", "expected_value": 2, "operator": "equals" }` |
| `packet_loss` | Packet loss percentage (%) | `{ "type": "packet_loss", "expected_value": 0.01, "operator": "less_than" }` |
| `flow_frames_transmitted` | Frames sent on a flow | `{ "type": "flow_frames_transmitted", "flow_name": "f1", "expected_value": 100000, "operator": "greater_than" }` |
| `flow_frames_received` | Frames received on a flow | `{ "type": "flow_frames_received", "flow_name": "f1", "expected_value": 100000, "operator": "greater_than" }` |
| `port_frames_transmitted` | Frames sent on a port | `{ "type": "port_frames_transmitted", "port_name": "P1", "expected_value": 500000, "operator": "greater_than" }` |
| `port_link_status` | Port link state | `{ "type": "port_link_status", "port_name": "P1", "expected_value": "up", "operator": "equals" }` |
| `bgp_route_count` | Routes learned via BGP | `{ "type": "bgp_route_count", "expected_value": 100, "operator": "greater_than" }` |
| `latency_avg` | Average latency (ns) | `{ "type": "latency_avg", "flow_name": "f1", "expected_value": 10000, "operator": "less_than" }` |

---

## How to Use

### Step 1: Prepare OTG Configuration

Create or generate an OTG configuration (JSON):

```bash
# Option A: Use otg-config-generator skill
/otg-config-generator
# User: "Create BGP test with 2 ports, AS 101 and AS 102..."
# Output: bgp_config.json

# Option B: Convert from IxNetwork
/ixnetwork-to-keng-converter
# User: "Convert this IxNetwork RestPy code to OTG..."
# Output: otg_config.json
```

### Step 2: Create Infrastructure YAML

Define controller, ports, and test parameters:

```yaml
controller:
  ip: "localhost"
  port: 8443
  protocol: "https"

ports:
  - name: "P1"
    location: "1/1"
  - name: "P2"
    location: "1/2"

test_config:
  duration_seconds: 60
  metrics_interval_seconds: 5
  stop_on_failure: false
```

### Step 3: Generate Script

Invoke the skill:

```bash
/snappi-script-generator
```

Provide:
- OTG configuration (file path or JSON string)
- Infrastructure YAML (file path or content)
- Assertions (optional, as JSON array)
- Test intent (brief description)

### Step 4: Run the Script

```bash
pip install snappi
python test_bgp.py
```

**Interactive mode:** Press Enter to proceed through each phase
**Silent mode:** Script executes autonomously (ideal for CI/CD)

---

## Common Patterns

### 1. Simple Port-to-Port Test
```
Config: 2 ports, 1 flow
Rate: 1000 pps
Duration: 30 seconds
Assertions: TX frames > 30000
```

### 2. VLAN-Tagged Traffic Test
```
Config: 2 ports with VLAN 100 interface, 1 flow with VLAN headers
Rate: 1000 pps
Duration: 60 seconds
Assertions: Port RX frames > 60000, packet loss < 0.01%
Packet structure: Ethernet → VLAN(id=100) → IPv4 → UDP
```

### 3. BGP Convergence Test
```
Config: 2 ports with BGP devices and routes
Rate: 1000 pps per flow
Duration: 60 seconds, metrics every 5s
Assertions: BGP sessions up (2), packet loss < 0.01%
Protocol wait: 30 seconds for BGP convergence
```

### 4. Multi-Protocol Convergence (BGP + ISIS)
```
Config: 2 ports with BGP and ISIS devices
Duration: 90 seconds (30s BGP + 40s ISIS + 20s traffic)
Assertions: BGP sessions up (2), ISIS adjacencies (2)
Protocol wait: Composite (BGP 30s + ISIS 40s)
```

### 5. BGP Route Aggregation Test
```
Config: BGP peers advertising multiple route ranges (500+ routes)
Rate: 1000 pps
Duration: 120 seconds
Assertions: BGP route count > 500, convergence < 60s
```

---

## Output Examples

### Generated Script Structure

```python
#!/usr/bin/env python3
"""
Snappi Test Script
Generated for: BGP convergence test
Controller: https://localhost:8443
"""

import snappi
import json
import time
import sys
from datetime import datetime

# ============================================================================
# Configuration (EMBEDDED in script for portability)
# ============================================================================

API_LOCATION = "https://localhost:8443"
TEST_DURATION = 60
METRICS_INTERVAL = 5
STOP_ON_FAILURE = False

# OTG Configuration (embedded JSON)
OTG_CONFIG_JSON = r'''{...}'''

# Assertions
ASSERTIONS = [...]

# ============================================================================
# API Functions
# ============================================================================

def connect_api(location, max_retries=3, backoff_factor=2):
    # Connection with exponential backoff retry
    ...

def load_config(api, config_json):
    # Load and validate OTG configuration
    ...

def start_protocols(api, config, wait_time=30):
    # Start all protocols with convergence wait
    ...

def start_traffic(api):
    # Initiate traffic transmission
    ...

def collect_metrics(api, flows, interval, duration):
    # Real-time metrics collection and display
    ...

def validate_assertions(metrics_data, assertions):
    # Assertion validation with detailed results
    ...

def stop_traffic(api):
    # Graceful traffic stop
    ...

def stop_protocols(api):
    # Protocol shutdown
    ...

def save_report(results):
    # JSON report generation
    ...

# ============================================================================
# Main Test Execution
# ============================================================================

def main():
    # Full test workflow with error handling
    ...

if __name__ == "__main__":
    main()
```

### Console Output

```
================================================================================
Snappi OTG Traffic Test
================================================================================

[Attempt 1/3] Connecting to https://localhost:8443...
✓ Connected successfully

[Step 1] Loading configuration...
✓ Configuration loaded (2 ports, 1 flow)

[Step 2] Starting protocols...
  Waiting 30 seconds for protocol convergence...
✓ Protocols started and converged

⏸ Press Enter to START TRAFFIC (or Ctrl+C to abort)...

[Step 3] Starting traffic...
✓ Traffic started

[Step 4] Collecting metrics (every 5s for 60s)...
────────────────────────────────────────────────────────────────────────────
Time       | TxFrames        | RxFrames        | Loss%      | Rate(pps)
────────────────────────────────────────────────────────────────────────────
5          | 5000            | 5000            | 0.00       | 1000.0
10         | 10000           | 10000           | 0.00       | 1000.0
...
✓ Metrics collection complete

[Step 5] Validating assertions...
  bgp_sessions equals 2: ✓ PASS (actual: 2)
  packet_loss less_than 0.01: ✓ PASS (actual: 0.00)
  flow_frames_transmitted greater_than 100000: ✓ PASS (actual: 60000)

[Step 6] Stopping traffic...
✓ Traffic stopped

[Step 7] Stopping protocols...
✓ Protocols stopped

✓ Report saved to test_report_20260317_103000.json

================================================================================
✓ Test completed successfully
================================================================================
```

### JSON Report

```json
{
  "timestamp": "2026-03-17T10:30:00",
  "controller": "https://localhost:8443",
  "duration": 60,
  "metrics": [
    {
      "timestamp": 5,
      "tx_frames": 5000,
      "rx_frames": 5000,
      "loss_pct": 0.0,
      "rate_pps": 1000.0
    },
    ...
  ],
  "assertions_passed": true,
  "assertions_detail": [
    {
      "type": "bgp_sessions",
      "expected": 2,
      "operator": "equals",
      "actual": 2,
      "passed": true
    },
    ...
  ]
}
```

---

## Reference Documentation

For detailed Snappi patterns and examples, see:

- **`references/protocol_examples.md`** — BGP, ISIS, LACP, VLAN, QinQ, route aggregation, communities, traffic rate patterns
- **`references/assertion_patterns.md`** — BGP convergence, ISIS adjacencies, packet loss, port metrics, latency, multi-protocol assertions
- **`references/github_snippets.md`** — Official Snappi repo code examples (initialization, serialization, metrics, traffic control, capture)

**Official Resources:**
- [Snappi SDK](https://github.com/open-traffic-generator/snappi) — Python client library
- [OTG Models](https://github.com/open-traffic-generator/models) — API schema and specification
- [OTG Examples](https://github.com/open-traffic-generator/otg-examples) — Complete lab examples with Containerlab

---

## Troubleshooting

### Issue: "Connection refused" error

**Cause:** Ixia-c controller is not running or unreachable

**Fix:**
```bash
# Deploy Ixia-c first using ixia-c-deployment skill
/ixia-c-deployment

# Or manually verify:
curl -kL https://localhost:8443/api/v1/config
```

### Issue: "Port not found" error

**Cause:** Port names in infrastructure.yaml don't match OTG configuration

**Fix:**
1. Verify port names in OTG config
2. Update infrastructure.yaml with correct names
3. Regenerate and rerun script

### Issue: BGP sessions not converging

**Cause:** Insufficient wait time for protocol convergence

**Fix:**
- Increase `wait_time` in `start_protocols()` (default: 30s)
- For ISIS, increase to 40s
- For multi-protocol: BGP 30s + ISIS 40s = 70s total

### Issue: "No metrics returned"

**Cause:** Traffic not started or metrics request incorrect

**Fix:**
```python
# Ensure traffic is started before metrics collection
start_traffic(api)
time.sleep(2)  # Wait for traffic to stabilize

# Verify metrics request
req = snappi.MetricsRequest()
req.choice = req.FLOW  # or PORT or DEVICE
```

### Issue: JSON parsing error

**Cause:** OTG configuration is malformed

**Fix:**
```bash
# Validate JSON syntax
python -m json.tool bgp_config.json

# Regenerate using otg-config-generator
/otg-config-generator
```

---

## Files

- `SKILL.md` — Skill definition with workflow, patterns, and examples
- `README.md` — This file (user guide + troubleshooting)
- `references/` — Protocol examples, assertion patterns, GitHub snippets
  - `protocol_examples.md` — BGP, ISIS, LACP, VLAN, QinQ patterns
  - `assertion_patterns.md` — Comprehensive assertion and validation patterns
  - `github_snippets.md` — Official Snappi repository code examples

---

## Next Steps

1. **Prepare OTG config** — Generate using `/otg-config-generator` or convert with `/ixnetwork-to-keng-converter`
2. **Create infrastructure.yaml** — Define controller, ports, test parameters
3. **Invoke skill** — `/snappi-script-generator` with config + infrastructure
4. **Execute script** — `python test_xxx.py` with interactive or silent mode
5. **Parse results** — JSON report available for CI/CD integration or analysis

---

**Status**: ✅ Production-Ready | **Version**: 1.1 | **Last Updated**: 2026-03-17
