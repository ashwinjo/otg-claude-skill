#!/usr/bin/env python3
"""
Snappi Test Script: B2B Dataplane 100% Line Rate
Generated for: Back-to-back traffic testing at maximum throughput
Controller: https://localhost:8443 (self-signed certificate)
Deployment: Docker Compose (ixia-c-te-a, ixia-c-te-b with veth pair)
"""

import snappi
import json
import time
import sys
import argparse
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

API_LOCATION = "https://localhost:8443"
TEST_DURATION = 30          # seconds
METRICS_INTERVAL = 1        # collect metrics every N seconds
STOP_ON_FAILURE = False

# ============================================================================
# OTG Configuration (embedded from otg_config.json)
# ============================================================================

OTG_CONFIG_JSON = r'''{
  "ports": [
    {
      "name": "port-1",
      "location": "veth-a"
    },
    {
      "name": "port-2",
      "location": "veth-b"
    }
  ],
  "flows": [
    {
      "name": "flow-1to2",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "port-1",
          "rx_names": [
            "port-2"
          ]
        }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "src": {
              "choice": "value",
              "value": "00:00:00:00:00:01"
            },
            "dst": {
              "choice": "value",
              "value": "00:00:00:00:00:02"
            }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 64
      },
      "rate": {
        "choice": "pps",
        "pps": 14880952
      },
      "duration": {
        "choice": "continuous"
      },
      "metrics": {
        "enable": true
      }
    },
    {
      "name": "flow-2to1",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "port-2",
          "rx_names": [
            "port-1"
          ]
        }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "src": {
              "choice": "value",
              "value": "00:00:00:00:00:02"
            },
            "dst": {
              "choice": "value",
              "value": "00:00:00:00:00:01"
            }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 64
      },
      "rate": {
        "choice": "pps",
        "pps": 14880952
      },
      "duration": {
        "choice": "continuous"
      },
      "metrics": {
        "enable": true
      }
    }
  ]
}'''

# ============================================================================
# API Functions
# ============================================================================

def connect_api(location, max_retries=3, backoff_factor=2):
    """
    Connect to OTG API with exponential backoff retry logic.
    Uses verify=False to accept self-signed certificates (ixia-c default).
    """
    for attempt in range(max_retries):
        try:
            print(f"[Attempt {attempt+1}/{max_retries}] Connecting to {location}...")
            api = snappi.api(location=location, verify=False)
            print("✓ Connected successfully\n")
            return api
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"✗ Connection failed: {e}")
                print(f"  Retrying in {wait_time} seconds...\n")
                time.sleep(wait_time)
            else:
                print(f"✗ Failed to connect after {max_retries} attempts")
                raise

def load_config(api, config_json):
    """
    Load OTG configuration into traffic generator.
    Uses deserialize() method (NOT loads()).
    """
    print("[Step 1] Loading OTG configuration...")
    try:
        config = snappi.Config()
        config.deserialize(config_json)
        api.set_config(config)
        print(f"✓ Configuration loaded ({len(config.ports)} ports, {len(config.flows)} flows)\n")
        return config
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        raise

def start_traffic(api):
    """
    Start traffic transmission on all flows.
    """
    print("[Step 2] Starting traffic transmission...")
    try:
        control_state = snappi.ControlState()
        control_state.traffic.choice = "flow_transmit"
        control_state.traffic.flow_transmit.state = "start"
        api.set_control_state(control_state)
        print("✓ Traffic started\n")
    except Exception as e:
        print(f"✗ Failed to start traffic: {e}")
        raise

def collect_metrics(api, flows, interval, duration):
    """
    Collect and display port and flow metrics at regular intervals.
    """
    print(f"[Step 3] Collecting metrics (interval: {interval}s, duration: {duration}s)")
    print("-" * 100)
    print(f"{'Time(s)':<10} | {'Flow':<12} | {'TxFrames':<15} | {'RxFrames':<15} | {'Loss%':<10}")
    print("-" * 100)

    metrics_data = []
    elapsed = 0

    try:
        while elapsed < duration:
            time.sleep(interval)
            elapsed += interval

            # Collect flow metrics
            req = snappi.MetricsRequest()
            req.choice = req.FLOW  # CORRECT: use req.choice, NOT MetricsRequest.FlowMetricState
            resp = api.get_metrics(req)

            for flow_metric in resp.flow_metrics:
                flow_name = flow_metric.name
                tx = flow_metric.frames_tx
                rx = flow_metric.frames_rx
                loss_pct = ((tx - rx) / tx * 100) if tx > 0 else 0

                metrics_data.append({
                    'timestamp': elapsed,
                    'flow': flow_name,
                    'tx_frames': tx,
                    'rx_frames': rx,
                    'loss_pct': loss_pct
                })

                print(f"{elapsed:<10} | {flow_name:<12} | {tx:<15} | {rx:<15} | {loss_pct:<10.2f}")

        print("-" * 100)
        print("✓ Metrics collection complete\n")
        return metrics_data
    except Exception as e:
        print(f"✗ Failed to collect metrics: {e}")
        raise

def stop_traffic(api):
    """
    Stop traffic transmission.
    """
    print("[Step 4] Stopping traffic...")
    try:
        control_state = snappi.ControlState()
        control_state.traffic.choice = "flow_transmit"
        control_state.traffic.flow_transmit.state = "stop"
        api.set_control_state(control_state)
        print("✓ Traffic stopped\n")
    except Exception as e:
        print(f"✗ Failed to stop traffic: {e}")

def generate_report(metrics_data):
    """
    Generate and save test report.
    """
    print("[Step 5] Generating test report...")

    # Calculate summary statistics
    total_tx = sum(m['tx_frames'] for m in metrics_data)
    total_rx = sum(m['rx_frames'] for m in metrics_data)
    total_loss = total_tx - total_rx
    loss_pct = (total_loss / total_tx * 100) if total_tx > 0 else 0
    duration = metrics_data[-1]['timestamp'] if metrics_data else 0
    avg_rate = (total_rx / duration) if duration > 0 else 0

    report = {
        'timestamp': datetime.now().isoformat(),
        'test_config': {
            'controller': API_LOCATION,
            'duration_seconds': TEST_DURATION,
            'metrics_interval_seconds': METRICS_INTERVAL
        },
        'summary': {
            'total_frames_transmitted': total_tx,
            'total_frames_received': total_rx,
            'total_frames_lost': total_loss,
            'loss_percentage': round(loss_pct, 4),
            'average_throughput_pps': round(avg_rate, 2),
            'peak_throughput_pps': round(max((m['rx_frames'] / METRICS_INTERVAL) for m in metrics_data) if metrics_data else 0, 2)
        },
        'per_flow_metrics': metrics_data
    }

    # Save to JSON file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Report saved to: {report_file}\n")

    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Frames Transmitted: {total_tx:,}")
    print(f"Total Frames Received:    {total_rx:,}")
    print(f"Total Frames Lost:        {total_loss:,}")
    print(f"Loss Percentage:          {loss_pct:.4f}%")
    print(f"Average Throughput:       {avg_rate:.2f} pps")
    print(f"Peak Throughput:          {report['summary']['peak_throughput_pps']:.2f} pps")
    print("=" * 80)

    return report_file, report

# ============================================================================
# Main Test Execution
# ============================================================================

def main(auto_start=False):
    """
    Main test execution flow.

    Args:
        auto_start (bool): Skip interactive prompt and start test immediately
    """
    print("=" * 80)
    print("Snappi B2B Dataplane Test @ 100% Line Rate")
    print("=" * 80)
    print(f"Controller: {API_LOCATION}")
    print(f"Duration: {TEST_DURATION} seconds")
    print(f"Mode: {'Auto-start' if auto_start else 'Interactive'}")
    print("=" * 80)
    print()

    api = None
    try:
        # Connect to controller
        api = connect_api(API_LOCATION)

        # Load OTG configuration
        config = load_config(api, OTG_CONFIG_JSON)

        # Start traffic (no protocols in dataplane-only test)
        start_traffic(api)

        # Interactive prompt (skip if auto_start is True)
        if not auto_start:
            input("⏸ Press Enter to START TEST DURATION (or Ctrl+C to abort)...")
            print()
        else:
            print("(Auto-start mode: skipping interactive prompt)\n")

        # Collect metrics during test
        metrics_data = collect_metrics(api, config.flows, METRICS_INTERVAL, TEST_DURATION)

        # Stop traffic
        stop_traffic(api)

        # Generate report
        report_file, report = generate_report(metrics_data)

        print("\n✓ Test completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    finally:
        # Always cleanup
        if api:
            try:
                stop_traffic(api)
            except:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Snappi B2B Dataplane Test @ 100% Line Rate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_b2b_dataplane.py              # Interactive mode (prompt for start)
  python3 test_b2b_dataplane.py --auto-start # Auto-start (skip prompt, run immediately)
  echo "" | python3 test_b2b_dataplane.py    # Non-interactive mode with piped input
        """
    )
    parser.add_argument(
        "--auto-start",
        action="store_true",
        help="Skip interactive prompt and start test immediately"
    )

    args = parser.parse_args()
    main(auto_start=args.auto_start)
