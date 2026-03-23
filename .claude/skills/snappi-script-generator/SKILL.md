---
name: snappi-script-generator
description: |
  Generate standalone, production-ready Python Snappi scripts from OTG configurations and infrastructure specifications.

  Use this skill whenever you need to:
  - Convert OTG/KENG JSON configurations into executable Snappi test scripts
  - Create traffic testing scripts that run against any OTG-compliant traffic generator (Ixia-c, etc.)
  - Generate scripts that handle protocol setup, traffic control, metrics collection, and assertions
  - Build reusable test automation with interactive prompts (or silent execution with JSON reports)
  - Implement error handling, retry logic, and graceful cleanup in traffic test scripts

  The skill takes OTG configuration + infrastructure YAML and produces a fully functional, stand-alone Python script ready to execute immediately.
compatibility: Requires snappi SDK (pip install snappi), OTG configuration JSON, infrastructure YAML
---

# Snappi Script Generator

Generate executable Python Snappi scripts from OTG configurations and infrastructure specifications.

## How It Works

You provide:
1. **OTG Configuration** (JSON from otg-config-generator or file path)
2. **Infrastructure YAML** (controller IP, port mappings, test parameters)
3. **Testing Options** (assertions, test duration, metrics intervals)

The skill produces a **standalone Python script** that:
- Connects to the traffic generator controller
- Loads and validates the OTG configuration
- Starts all protocols (BGP, ISIS, etc.)
- Manages traffic flows with interactive prompts
- Collects and displays real-time metrics
- Validates assertions (packet loss, session count, etc.)
- Handles errors with exponential backoff retry
- Gracefully cleans up resources

## Workflow

### Step 1: Define Infrastructure (YAML)

Create an infrastructure file (e.g., `infrastructure.yaml`):

```yaml
controller:
  ip: "10.0.0.1"
  port: 8443
  protocol: "https"

ports:
  - name: "P1"
    location: "eth1"    # or "1/1/1" or "card/port" format
  - name: "P2"
    location: "eth2"

test_config:
  duration_seconds: 60
  metrics_interval_seconds: 5
  stop_on_failure: false
```

**Fields:**
- `controller.ip` — API server IP
- `controller.port` — API server port (default 8443)
- `controller.protocol` — http or https (default https)
- `ports[].name` — Logical port name (from OTG config)
- `ports[].location` — Physical port identifier
- `test_config.duration_seconds` — Test duration
- `test_config.metrics_interval_seconds` — Metrics polling interval
- `test_config.stop_on_failure` — Stop test if assertion fails

### Step 2: Specify Traffic Rate

Traffic flows can specify rate in multiple formats:

```python
# Packets per second
flow.rate.pps = 1000

# Percentage of line rate (0-100%)
flow.rate.percentage = 50

# Bytes per second
flow.rate.bps = 1000000

# Fixed number of packets (for test termination)
flow.duration.fixed_packets.packets = 1000000

# Fixed test duration
flow.duration.fixed_seconds.seconds = 60

# Continuous traffic
flow.duration.continuous.gap = 12  # Inter-packet gap in bytes
```

**Rate choice:** Use `pps` for packet-level control, `percentage` for line-rate ratios, `bps` for throughput-based testing.

### Step 3: Specify Assertions (Optional, Configurable)

Assertions are configurable and can be passed in the generation request. Examples:

```json
{
  "assertions": [
    {
      "type": "bgp_sessions",
      "expected_value": 2,
      "operator": "equals"
    },
    {
      "type": "packet_loss",
      "expected_value": 0.01,
      "operator": "less_than"
    },
    {
      "type": "flow_frames_transmitted",
      "flow_name": "flow1",
      "expected_value": 100000,
      "operator": "greater_than"
    }
  ]
}
```

**Supported assertion types:**
- `bgp_sessions` — Expected number of BGP sessions up
- `isis_sessions` — Expected number of ISIS adjacencies
- `packet_loss` — Maximum acceptable packet loss percentage
- `flow_frames_transmitted` — Minimum frames expected on a flow
- `flow_frames_received` — Minimum frames expected received on a flow
- `port_frames_transmitted` — Minimum frames on a specific port
- `port_link_status` — Port link state (up/down)
- `bgp_route_count` — Number of routes learned via BGP
- `latency_avg` — Maximum average latency (ms)

### Step 3: Generate the Script

Provide to the skill:
- **OTG Config** (path or JSON string)
- **Infrastructure YAML** (path or content)
- **Assertions** (optional; if not provided, script skips assertions)
- **Test Intent** (e.g., "Run BGP test for 60 seconds, collect metrics every 5 seconds")

The skill generates a standalone Python script with:

```python
#!/usr/bin/env python3
"""
Snappi Test Script
Generated for: BGP convergence test
Controller: https://10.0.0.1:8443
"""

import snappi
import json
import time
import sys
from datetime import datetime

# ============================================================================
# Configuration (EMBEDDED in script for portability)
# ============================================================================

API_LOCATION = "https://10.0.0.1:8443"
TEST_DURATION = 60
METRICS_INTERVAL = 5
STOP_ON_FAILURE = False

# OTG Configuration (embedded JSON)
OTG_CONFIG_JSON = r'''{
  "ports": [...],
  "devices": [...],
  "flows": [...]
}'''

# Assertions
ASSERTIONS = [
  {"type": "bgp_sessions", "expected_value": 2, "operator": "equals"},
  {"type": "packet_loss", "expected_value": 0.01, "operator": "less_than"}
]

# ============================================================================
# API Functions
# ============================================================================

def connect_api(location, max_retries=3, backoff_factor=2):
    """
    Connect to OTG API with exponential backoff retry logic
    """
    for attempt in range(max_retries):
        try:
            print(f"[Attempt {attempt+1}/{max_retries}] Connecting to {location}...")
            # verify=False accepts self-signed certs (default in ixia-c)
            # For production, replace with: verify="/path/to/ca-bundle.crt"
            api = snappi.api(location=location, verify=False)
            print("✓ Connected successfully")
            return api
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"✗ Connection failed: {e}")
                print(f"  Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"✗ Failed to connect after {max_retries} attempts")
                raise

def load_config(api, config_json):
    """
    Load OTG configuration into traffic generator
    """
    print("\n[Step 1] Loading configuration...")
    try:
        config = snappi.Config()
        config.loads(config_json)
        api.set_config(config)
        print(f"✓ Configuration loaded ({len(config.ports)} ports, {len(config.flows)} flows)")
        return config
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        raise

def wait_for_bgp_convergence(api, expected_sessions, timeout=60, poll_interval=5):
    """
    Poll BGP session state until expected session count is reached or timeout expires.
    Preferred over a fixed sleep — returns as soon as BGP is up.
    """
    elapsed = 0
    while elapsed < timeout:
        count = get_bgp_session_count(api)
        print(f"  BGP sessions up: {count}/{expected_sessions} ({elapsed}s elapsed)", end='\r')
        if count >= expected_sessions:
            print(f"\n✓ BGP converged ({count} sessions up in {elapsed}s)")
            return True
        time.sleep(poll_interval)
        elapsed += poll_interval
    print(f"\n✗ BGP convergence timeout ({timeout}s): only {get_bgp_session_count(api)}/{expected_sessions} sessions up")
    return False

def start_protocols(api, config, wait_time=30, expected_bgp_sessions=0):
    """
    Start all protocols (BGP, ISIS, etc.).
    If expected_bgp_sessions > 0, polls for convergence instead of sleeping blindly.
    """
    print("\n[Step 2] Starting protocols...")
    try:
        # Check if configuration has devices with protocols
        protocol_count = 0
        for device in config.devices:
            if hasattr(device, 'bgp') and device.bgp:
                protocol_count += 1
            if hasattr(device, 'isis') and device.isis:
                protocol_count += 1

        if protocol_count == 0:
            print("  (No protocols to start)")
            return

        # Start all protocols
        # CORRECT API: use cs.protocol.choice + cs.protocol.all.state
        # WRONG (will raise AttributeError): snappi.ControlState.Protocol.start
        state = snappi.ControlState()
        state.protocol.choice = state.protocol.ALL
        state.protocol.all.state = state.protocol.all.START
        api.set_control_state(state)

        if expected_bgp_sessions > 0:
            # Poll until BGP sessions are up (faster than a fixed sleep)
            wait_for_bgp_convergence(api, expected_bgp_sessions, timeout=wait_time)
        else:
            print(f"  Waiting {wait_time} seconds for protocol convergence...")
            for i in range(wait_time, 0, -1):
                print(f"    {i} seconds remaining...", end='\r')
                time.sleep(1)

        print("✓ Protocols started and converged")
    except Exception as e:
        print(f"✗ Failed to start protocols: {e}")
        raise

def get_bgp_session_count(api):
    """
    Get current BGP session count from live metrics
    """
    try:
        req = snappi.MetricsRequest()
        req.choice = req.DEVICE
        resp = api.get_metrics(req)

        bgp_up = 0
        for metric in resp.device_metrics:
            if hasattr(metric, 'bgp_session'):
                for session in metric.bgp_session:
                    if session.session_state in ('up', 'established'):
                        bgp_up += 1
        return bgp_up
    except:
        return 0

def start_traffic(api):
    """
    Start traffic transmission
    """
    print("\n[Step 3] Starting traffic...")
    try:
        control_state = snappi.ControlState()
        control_state.traffic.flow_transmit.state = "start"
        api.set_control_state(control_state)
        print("✓ Traffic started")
    except Exception as e:
        print(f"✗ Failed to start traffic: {e}")
        raise

def collect_metrics(api, flows, interval, duration):
    """
    Collect and display metrics at regular intervals
    """
    print(f"\n[Step 4] Collecting metrics (every {interval}s for {duration}s)...")
    print("-" * 80)
    print(f"{'Time':<10} | {'TxFrames':<15} | {'RxFrames':<15} | {'Loss%':<10} | {'Rate(pps)':<15}")
    print("-" * 80)

    metrics_data = []
    elapsed = 0

    try:
        while elapsed < duration:
            time.sleep(interval)
            elapsed += interval

            # Get flow metrics
            req = snappi.MetricsRequest()
            req.choice = req.FLOW
            resp = api.get_metrics(req)

            total_tx = 0
            total_rx = 0

            for flow_metric in resp.flow_metrics:
                tx = flow_metric.frames_tx
                rx = flow_metric.frames_rx
                total_tx += tx
                total_rx += rx

                loss_pct = ((tx - rx) / tx * 100) if tx > 0 else 0
                rate_pps = (rx / interval) if interval > 0 else 0

                metrics_data.append({
                    'timestamp': elapsed,
                    'tx_frames': tx,
                    'rx_frames': rx,
                    'loss_pct': loss_pct,
                    'rate_pps': rate_pps
                })

                print(f"{elapsed:<10} | {tx:<15} | {rx:<15} | {loss_pct:<10.2f} | {rate_pps:<15.0f}")

        print("-" * 80)
        print("✓ Metrics collection complete")
        return metrics_data
    except Exception as e:
        print(f"✗ Failed to collect metrics: {e}")
        raise

def validate_assertions(api, metrics_data, assertions):
    """
    Validate test assertions against live metrics and collected data
    """
    if not assertions:
        print("\n(No assertions to validate)")
        return True

    print(f"\n[Step 5] Validating assertions...")
    all_passed = True

    for assertion in assertions:
        assertion_type = assertion.get('type')
        expected = assertion.get('expected_value')
        operator = assertion.get('operator')

        passed = False
        actual = None

        if assertion_type == 'packet_loss':
            # Calculate average packet loss from collected metrics
            if metrics_data:
                avg_loss = sum(m.get('loss_pct', 0) for m in metrics_data) / len(metrics_data)
                actual = avg_loss
                if operator == 'less_than':
                    passed = avg_loss < expected

        elif assertion_type == 'bgp_sessions':
            # Check live BGP session count from controller
            actual = get_bgp_session_count(api)
            if operator == 'equals':
                passed = actual == expected
            elif operator == 'greater_than':
                passed = actual > expected
            elif operator == 'less_than':
                passed = actual < expected

        elif assertion_type == 'flow_frames_transmitted':
            # Check if frames transmitted on flow
            if metrics_data and metrics_data[-1].get('tx_frames', 0) > expected:
                actual = metrics_data[-1].get('tx_frames', 0)
                passed = True

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {assertion_type} {operator} {expected}: {status} (actual: {actual})")

        if not passed:
            all_passed = False

    return all_passed

def stop_traffic(api):
    """
    Stop traffic transmission
    """
    print("\n[Step 6] Stopping traffic...")
    try:
        control_state = snappi.ControlState()
        control_state.traffic.flow_transmit.state = "stop"
        api.set_control_state(control_state)
        print("✓ Traffic stopped")
    except Exception as e:
        print(f"✗ Failed to stop traffic: {e}")

def stop_protocols(api):
    """
    Stop all protocols
    """
    print("\n[Step 7] Stopping protocols...")
    try:
        state = snappi.ControlState()
        state.protocol.choice = state.protocol.ALL
        state.protocol.all.state = state.protocol.all.STOP
        api.set_control_state(state)
        print("✓ Protocols stopped")
    except Exception as e:
        print(f"✗ Failed to stop protocols: {e}")

def save_report(results):
    """
    Save test results to JSON report
    """
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Report saved to {report_file}")
    return report_file

# ============================================================================
# Main Test Execution
# ============================================================================

def main():
    """
    Main test execution flow with interactive prompts
    """
    print("=" * 80)
    print("Snappi OTG Traffic Test")
    print("=" * 80)

    api = None
    try:
        # Step 1: Connect
        api = connect_api(API_LOCATION)

        # Step 2: Load config
        config = load_config(api, OTG_CONFIG_JSON)

        # Step 3: Start protocols
        start_protocols(api)

        # Step 4: Interactive prompt before starting traffic
        input("\n⏸ Press Enter to START TRAFFIC (or Ctrl+C to abort)...")
        start_traffic(api)

        # Step 5: Collect metrics
        metrics_data = collect_metrics(api, config.flows, METRICS_INTERVAL, TEST_DURATION)

        # Step 6: Validate assertions
        assertions_passed = validate_assertions(api, metrics_data, ASSERTIONS)

        if not assertions_passed and STOP_ON_FAILURE:
            print("\n✗ Test FAILED (assertions did not pass)")
            sys.exit(1)

        # Step 7: Cleanup
        stop_traffic(api)
        stop_protocols(api)

        # Step 8: Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'controller': API_LOCATION,
            'duration': TEST_DURATION,
            'metrics': metrics_data,
            'assertions_passed': assertions_passed
        }
        save_report(report)

        print("\n" + "=" * 80)
        print("✓ Test completed successfully")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    finally:
        # Always cleanup
        if api:
            try:
                stop_traffic(api)
                stop_protocols(api)
            except:
                pass

if __name__ == "__main__":
    main()
```

## Step 4: Run the Script

```bash
# Install dependencies (pin to a tested version to avoid API changes between releases)
pip install snappi==1.22.0   # replace with the version matching your ixia-c controller

# Run the generated script
python test_bgp.py

# Follow interactive prompts:
# - Press Enter to start traffic
# - Watch real-time metrics
# - Assertions validated automatically
# - Results saved to JSON report
```

## Output

The script produces:

**Console Output:**
```
================================================================================
Snappi OTG Traffic Test
================================================================================

[Attempt 1/3] Connecting to https://10.0.0.1:8443...
✓ Connected successfully

[Step 1] Loading configuration...
✓ Configuration loaded (2 ports, 2 flows)

[Step 2] Starting protocols...
  Waiting 30 seconds for protocol convergence...
    1 seconds remaining...
✓ Protocols started and converged

⏸ Press Enter to START TRAFFIC (or Ctrl+C to abort)...

[Step 3] Starting traffic...
✓ Traffic started

[Step 4] Collecting metrics (every 5s for 60s)...
...
```

**JSON Report (`test_report_YYYYMMDD_HHMMSS.json`):**
```json
{
  "timestamp": "2026-03-17T10:30:00",
  "controller": "https://10.0.0.1:8443",
  "duration": 60,
  "metrics": [
    {
      "timestamp": 5,
      "tx_frames": 50000,
      "rx_frames": 50000,
      "loss_pct": 0.0,
      "rate_pps": 10000.0
    }
  ],
  "assertions_passed": true
}
```

## Common Patterns

### Simple Port-to-Port Test
```
Config: 2 ports, 1 flow
Infrastructure: Simple point-to-point
Assertions: Check frame count
Duration: 30 seconds
```

### VLAN-Tagged Traffic Test
```
Config: 2 ports with VLAN 100 interface, 1 flow with VLAN headers
Infrastructure: Lab with controller + 2 ports
Assertions: Port RX frames > 100000, packet loss < 0.01%
Duration: 60 seconds
Packet structure: Ethernet → VLAN(id=100) → IPv4 → UDP
```

### BGP Convergence Test
```
Config: 2 ports with BGP devices and routes
Infrastructure: Lab with controller + 2 ports
Assertions: BGP sessions up (2), packet loss < 0.01%
Duration: 60 seconds, metrics every 5s
Protocol wait: 30 seconds for BGP convergence
```

### Multi-Protocol Convergence Test (BGP + ISIS)
```
Config: 2 ports with BGP and ISIS devices
Infrastructure: Lab with controller + 2 ports + protocol engine
Assertions: BGP sessions up (2), ISIS adjacencies (2)
Duration: 90 seconds (30s for each protocol to converge)
Setup: Start protocols with 40s wait, then traffic
Protocol wait: Use composite wait for multi-protocol (BGP 30s + ISIS 40s)
```

### Multi-Flow Streaming Test
```
Config: 2 ports with 10 bidirectional flows
Infrastructure: High-speed test setup
Assertions: All flows transmitting, latency < 10ms, no packet loss
Duration: 120 seconds, metrics every 2s
```

### BGP Route Aggregation Test
```
Config: 2 ports with BGP peers advertising multiple route ranges
Infrastructure: Lab with controller + 2 ports
Assertions: BGP route count > 500, convergence time < 60s
Duration: 120 seconds
Flow: Traffic to specific route (e.g., 10.0.0.0/24)
```

## Known Pitfalls (Validated Against ixia-c keng-controller:1.48.0-5)

Apply these rules to every generated script — they have caused real test failures.

### ControlState API: use .choice + .all.state, not .Protocol class attribute
```python
# CORRECT
cs = snappi.ControlState()
cs.protocol.choice = cs.protocol.ALL
cs.protocol.all.state = cs.protocol.all.START  # or .STOP
api.set_control_state(cs)

# WRONG — AttributeError: type object 'ControlState' has no attribute 'Protocol'
cs.protocol.state = snappi.ControlState.Protocol.start  # DO NOT USE
```

### BGPv4 session_state value is "up", not "established"
When polling `get_metrics(req.BGPV4)`, the `session_state` field returns `"up"` (not `"established"`) on ixia-c. Always check for both to be safe:
```python
if m.session_state in ("up", "established"):
    bgp_up += 1
```

### Flow duration: always use "continuous", stop traffic manually
`fixed_seconds` duration causes keng-controller (v1.48.0-5) to crash-restart when flows self-terminate, dropping the API connection mid-test. Use `continuous` duration and stop traffic programmatically:
```python
# In OTG config: "duration": { "choice": "continuous" }
# In script: run metrics loop for desired duration, then call stop_traffic()
```

### docker cp config.yaml: always chmod 644 after copy
If the deployment script uses `docker cp` to inject `config.yaml` into the controller container, the file lands with mode 600 (root-owned, not readable by the controller process). The controller returns HTTP 500 `permission denied`. Always run after copy:
```bash
sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml
```

### Snappi Config API: use .deserialize(), not .loads()
The Python stdlib `json.loads()` is NOT available on snappi.Config objects. Use the correct Snappi API:
```python
# CORRECT
cfg = snappi.Config()
cfg.deserialize(otg_json_string)      # load JSON string into config
api.set_config(cfg)

json_output = cfg.serialize()          # export config as JSON string

# WRONG — AttributeError: 'Config' object has no attribute 'loads'
cfg.loads(json_string)  # DO NOT USE
```

### ixia-c-one: metric fields limitations (vs full CP+DP)
ixia-c-one (all-in-one bundle, keng-controller v1.48.0-5) does NOT support:
- Flow-level latency metrics (store_forward, cut_through, any mode) → **removed from config**
- Flow-level loss metrics → **removed from config**

These are supported in full ixia-c CP+DP deployment but NOT in the ixia-c-one container.

**Workaround:** Remove unsupported metric fields before pushing to ixia-c-one:
```python
# CORRECT for ixia-c-one
flow.metrics.enable = True            # basic frame counters only
# Do NOT set: flow.metrics.latency, flow.metrics.loss

# Collect metrics from port-level stats instead
port_metrics = api.get_metrics(req.PORT)
for pm in port_metrics.port_metrics:
    frames_tx = pm.frames_tx
    frames_rx = pm.frames_rx
    loss = frames_tx - frames_rx
```

**Prevention:** If generating for ixia-c-one target, filter the OTG config before `api.set_config()`:
```python
for flow in cfg.flows:
    if hasattr(flow, 'metrics'):
        flow.metrics.latency = None    # remove unsupported field
        # or better: only set .enable, omit others
```

## Error Handling

The generated script includes:
- **Exponential backoff retry** for connection failures
- **Graceful degradation** if protocols aren't available
- **Exception handling** with detailed error messages
- **Automatic cleanup** (stop traffic, stop protocols) on exit
- **Keyboard interrupt handling** (Ctrl+C gracefully exits)

## Future Enhancements

Once comfortable with the interactive prompts, evolution to:
- **Silent execution** (no prompts, just run)
- **Automated validation** (run assertions without user input)
- **Continuous monitoring** (monitor and alert on failures)
- **Parallel test runs** (execute multiple tests)
- **CI/CD integration** (GitHub Actions, Jenkins, etc.)

---

## Reference Documentation

For detailed Snappi patterns and advanced examples, see:

- **`references/protocol_examples.md`** — BGP, ISIS, LACP, VLAN, QinQ, route aggregation, communities, traffic rate patterns
- **`references/assertion_patterns.md`** — BGP convergence, ISIS adjacencies, packet loss, port metrics, latency, multi-protocol assertions
- **`references/github_snippets.md`** — Official Snappi repo code examples (initialization, serialization, metrics, traffic control, capture)

**Official Resources:**
- [Snappi SDK](https://github.com/open-traffic-generator/snappi) — Python client library
- [OTG Models](https://github.com/open-traffic-generator/models) — API schema and specification
- [OTG Examples](https://github.com/open-traffic-generator/otg-examples) — Complete lab examples with Containerlab

---

## Example Input to Skill

```
OTG Config: bgp_keng.json   (or paste the JSON inline)
Infrastructure YAML: infrastructure.yaml   (or provide inline)

Assertions:
- BGP sessions up: 2
- Packet loss: < 0.01%
- Tx frames on flow_p1_to_p2: > 100000

Test intent: "BGP convergence and bidirectional traffic test"
```

## Example Output from Skill

**Generated Script:** `test_bgp_keng.py` (standalone, ready to run)

```bash
python test_bgp_keng.py
# Executes with interactive prompts and generates test_report_20260317_103000.json
```
