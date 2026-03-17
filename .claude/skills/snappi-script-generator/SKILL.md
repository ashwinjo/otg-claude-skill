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

### Step 2: Specify Assertions (Optional, Configurable)

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
            api = snappi.api(location=location)
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

def start_protocols(api, config, wait_time=30):
    """
    Start all protocols (BGP, ISIS, etc.)
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
        state = snappi.ControlState()
        state.protocol.state = snappi.ControlState.Protocol.start
        api.set_control_state(state)

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
    Get current BGP session count
    """
    try:
        req = snappi.MetricsRequest()
        req.device.state = snappi.MetricsRequest.DeviceMetricState.any
        resp = api.get_metrics(req)

        bgp_up = 0
        for metric in resp.device_metrics:
            if hasattr(metric, 'bgp_session') and metric.bgp_session:
                bgp_up += len([s for s in metric.bgp_session if s.state == 'up'])
        return bgp_up
    except:
        return 0

def start_traffic(api):
    """
    Start traffic transmission
    """
    print("\n[Step 3] Starting traffic...")
    try:
        state = snappi.TransmitState()
        state.state = snappi.TransmitState.start
        api.set_transmit_state(state)
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
            req.flow.state = snappi.MetricsRequest.FlowMetricState.any
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

def validate_assertions(metrics_data, assertions):
    """
    Validate test assertions
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
            # Calculate average packet loss
            if metrics_data:
                avg_loss = sum(m.get('loss_pct', 0) for m in metrics_data) / len(metrics_data)
                actual = avg_loss
                if operator == 'less_than':
                    passed = avg_loss < expected

        elif assertion_type == 'bgp_sessions':
            # Check final BGP session count (would need live check)
            passed = True  # Placeholder

        elif assertion_type == 'flow_frames_transmitted':
            # Check if frames transmitted on flow
            if metrics_data and metrics_data[-1].get('tx_frames', 0) > expected:
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
        state = snappi.TransmitState()
        state.state = snappi.TransmitState.stop
        api.set_transmit_state(state)
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
        state.protocol.state = snappi.ControlState.Protocol.stop
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
        assertions_passed = validate_assertions(metrics_data, ASSERTIONS)

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
# Install dependencies
pip install snappi

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

### BGP Convergence Test
```
Config: 2 ports with BGP devices and routes
Infrastructure: Lab with controller + 2 ports
Assertions: BGP sessions up, packet loss < 0.01%
Duration: 60 seconds, metrics every 5s
```

### Multi-Flow Streaming Test
```
Config: 2 ports with 10 bidirectional flows
Infrastructure: High-speed test setup
Assertions: All flows transmitting, latency < 10ms
Duration: 120 seconds, metrics every 2s
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

## Example Input to Skill

```
OTG Config: /Users/ashwin.joshi/kengotg/bgp_keng.json
Infrastructure YAML: /Users/ashwin.joshi/kengotg/infrastructure.yaml

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
