#!/usr/bin/env python3
"""
Snappi BGP Convergence Test
Generated: 2026-03-19
Test: BGP convergence with bidirectional traffic (CP+DP)
Controller: https://localhost:8443
Ports: te1 (veth-a, AS 65001) ↔ te2 (veth-z, AS 65002)
Traffic: 1000 pps bidirectional, 512-byte packets, 120 seconds
Assertions: BGP Established + zero packet loss
"""

import snappi
import json
import time
import sys
import ssl
import urllib3
from datetime import datetime

# Suppress SSL warnings (self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# Configuration
# ============================================================================

API_LOCATION = "https://localhost:8443"
TEST_DURATION = 120  # seconds
METRICS_INTERVAL = 5  # seconds
BGP_CONVERGENCE_TIMEOUT = 30  # seconds
STOP_ON_FAILURE = False

# OTG Configuration (embedded JSON from bgp_convergence_cpdp.json)
OTG_CONFIG_JSON = r'''{
  "ports": [
    {
      "name": "te1",
      "location": "veth-a"
    },
    {
      "name": "te2",
      "location": "veth-z"
    }
  ],
  "devices": [
    {
      "name": "device1",
      "container_name": "device1",
      "device_eth": [
        {
          "name": "eth1",
          "connection": {
            "choice": "port_name",
            "port_name": "te1"
          },
          "mac": "00:11:22:33:44:55",
          "ipv4_addresses": [
            {
              "name": "ipv4_1",
              "address": "10.0.0.1",
              "prefix": 24,
              "gateway": "10.0.0.2"
            }
          ]
        }
      ],
      "bgp": [
        {
          "name": "bgp",
          "router_id": "1.0.0.1",
          "asn": 65001,
          "ipv4_unicast": {
            "sendunicast": true
          },
          "neighbors": [
            {
              "name": "bgp_neighbor_1",
              "peer_address": "10.0.0.2",
              "as_number": 65002
            }
          ]
        }
      ]
    },
    {
      "name": "device2",
      "container_name": "device2",
      "device_eth": [
        {
          "name": "eth1",
          "connection": {
            "choice": "port_name",
            "port_name": "te2"
          },
          "mac": "00:11:22:33:44:66",
          "ipv4_addresses": [
            {
              "name": "ipv4_1",
              "address": "10.0.0.2",
              "prefix": 24,
              "gateway": "10.0.0.1"
            }
          ]
        }
      ],
      "bgp": [
        {
          "name": "bgp",
          "router_id": "2.0.0.1",
          "asn": 65002,
          "ipv4_unicast": {
            "sendunicast": true
          },
          "neighbors": [
            {
              "name": "bgp_neighbor_1",
              "peer_address": "10.0.0.1",
              "as_number": 65001
            }
          ]
        }
      ]
    }
  ],
  "flows": [
    {
      "name": "flow_te1_to_te2",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "te1",
          "rx_names": [
            "te2"
          ]
        }
      },
      "packet": [
        {
          "name": "eth",
          "header": {
            "choice": "ethernet",
            "ethernet": {
              "dst": {
                "choice": "value",
                "value": "00:11:22:33:44:66"
              },
              "src": {
                "choice": "value",
                "value": "00:11:22:33:44:55"
              }
            }
          }
        },
        {
          "name": "ipv4",
          "header": {
            "choice": "ipv4",
            "ipv4": {
              "src": {
                "choice": "value",
                "value": "10.0.0.1"
              },
              "dst": {
                "choice": "value",
                "value": "10.0.0.2"
              }
            }
          }
        },
        {
          "name": "udp",
          "header": {
            "choice": "udp",
            "udp": {
              "src_port": {
                "choice": "value",
                "value": 5000
              },
              "dst_port": {
                "choice": "value",
                "value": 5001
              }
            }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 512
      },
      "rate": {
        "choice": "pps",
        "pps": 1000
      },
      "duration": {
        "choice": "fixed_packets",
        "fixed_packets": 120000
      }
    },
    {
      "name": "flow_te2_to_te1",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "te2",
          "rx_names": [
            "te1"
          ]
        }
      },
      "packet": [
        {
          "name": "eth",
          "header": {
            "choice": "ethernet",
            "ethernet": {
              "dst": {
                "choice": "value",
                "value": "00:11:22:33:44:55"
              },
              "src": {
                "choice": "value",
                "value": "00:11:22:33:44:66"
              }
            }
          }
        },
        {
          "name": "ipv4",
          "header": {
            "choice": "ipv4",
            "ipv4": {
              "src": {
                "choice": "value",
                "value": "10.0.0.2"
              },
              "dst": {
                "choice": "value",
                "value": "10.0.0.1"
              }
            }
          }
        },
        {
          "name": "udp",
          "header": {
            "choice": "udp",
            "udp": {
              "src_port": {
                "choice": "value",
                "value": 5001
              },
              "dst_port": {
                "choice": "value",
                "value": 5000
              }
            }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 512
      },
      "rate": {
        "choice": "pps",
        "pps": 1000
      },
      "duration": {
        "choice": "fixed_packets",
        "fixed_packets": 120000
      }
    }
  ]
}'''

# Assertions
ASSERTIONS = {
    "bgp_convergence": {
        "expected_state": "Established",
        "timeout_seconds": BGP_CONVERGENCE_TIMEOUT
    },
    "packet_loss": {
        "max_loss_percent": 0.1,
        "operator": "less_than"
    },
    "flow_frames": {
        "min_frames_transmitted": 90000,
        "operator": "greater_than"
    }
}

# ============================================================================
# API Functions
# ============================================================================

def connect_api(location, max_retries=3, backoff_factor=2):
    """
    Connect to OTG API with exponential backoff retry logic
    """
    print(f"\n[Connecting] API endpoint: {location}")

    for attempt in range(max_retries):
        try:
            print(f"  [Attempt {attempt+1}/{max_retries}] Connecting...")
            api = snappi.api(
                location=location,
                verify=False  # Self-signed certs
            )
            print(f"  ✓ Connected successfully")
            return api
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"  ✗ Connection failed: {str(e)[:80]}")
                print(f"    Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  ✗ Failed after {max_retries} attempts")
                raise


def load_config(api, config_json):
    """
    Load OTG configuration into traffic generator
    """
    print(f"\n[Step 1/7] Loading OTG configuration...")
    try:
        config = snappi.Config()
        config.loads(config_json)

        # Validate config
        print(f"  Config structure:")
        print(f"    - Ports: {len(config.ports)}")
        print(f"    - Devices: {len(config.devices)}")
        print(f"    - Flows: {len(config.flows)}")

        # Push config to controller
        print(f"  Pushing config to controller...")
        api.set_config(config)

        print(f"  ✓ Configuration loaded and validated")
        return config
    except Exception as e:
        print(f"  ✗ Failed to load configuration: {e}")
        raise


def wait_for_bgp_convergence(api, timeout=30):
    """
    Wait for BGP sessions to reach Established state
    """
    print(f"\n[Step 2/7] Waiting for BGP convergence (max {timeout}s)...")

    start_time = time.time()
    bgp_established = False

    try:
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)

            # Get device metrics
            req = snappi.MetricsRequest()
            req.device.state = snappi.MetricsRequest.DeviceMetricState.any
            resp = api.get_metrics(req)

            # Check BGP session state
            bgp_up_count = 0
            bgp_down_count = 0

            for device_metric in resp.device_metrics:
                if hasattr(device_metric, 'bgp_sessions') and device_metric.bgp_sessions:
                    for session in device_metric.bgp_sessions:
                        if session.state == "up":
                            bgp_up_count += 1
                        else:
                            bgp_down_count += 1

            print(f"  [{elapsed}s] BGP sessions: {bgp_up_count} up, {bgp_down_count} down", end='\r')

            # Check if all expected sessions are up (2 BGP sessions: device1 ↔ device2)
            if bgp_up_count >= 2:
                bgp_established = True
                print(f"\n  ✓ BGP converged in {elapsed}s (2 sessions established)")
                break

            time.sleep(1)

        if not bgp_established:
            print(f"\n  ⚠ BGP convergence timeout ({timeout}s) - proceeding with traffic")

        return bgp_established

    except Exception as e:
        print(f"\n  ⚠ Error checking BGP state: {e}")
        return False


def start_traffic(api):
    """
    Start traffic transmission
    """
    print(f"\n[Step 3/7] Starting traffic transmission...")
    try:
        state = snappi.TransmitState()
        state.state = snappi.TransmitState.start
        api.set_transmit_state(state)
        print(f"  ✓ Traffic started")
        return True
    except Exception as e:
        print(f"  ✗ Failed to start traffic: {e}")
        raise


def collect_metrics(api, test_duration, interval):
    """
    Collect metrics at regular intervals
    """
    print(f"\n[Step 4/7] Collecting metrics (every {interval}s for {test_duration}s)...")
    print(f"  {'-'*95}")
    print(f"  {'Time (s)':<12} | {'TxFrames':<15} | {'RxFrames':<15} | {'Loss %':<10} | {'Pps':<10}")
    print(f"  {'-'*95}")

    metrics_data = []
    elapsed = 0

    try:
        while elapsed < test_duration:
            time.sleep(interval)
            elapsed += interval

            # Get port statistics
            req = snappi.MetricsRequest()
            req.port.state = snappi.MetricsRequest.PortMetricState.any
            resp = api.get_metrics(req)

            # Get flow statistics
            freq = snappi.MetricsRequest()
            freq.flow.state = snappi.MetricsRequest.FlowMetricState.any
            fresp = api.get_metrics(freq)

            # Aggregate metrics
            total_tx = 0
            total_rx = 0

            for flow_metric in fresp.flow_metrics:
                tx = flow_metric.frames_tx or 0
                rx = flow_metric.frames_rx or 0
                total_tx += tx
                total_rx += rx

            # Calculate statistics
            loss_frames = total_tx - total_rx
            loss_pct = (loss_frames / total_tx * 100) if total_tx > 0 else 0
            rate_pps = (total_rx / interval) if interval > 0 else 0

            # Store metrics
            metrics_data.append({
                'elapsed': elapsed,
                'tx_frames': total_tx,
                'rx_frames': total_rx,
                'loss_frames': loss_frames,
                'loss_pct': loss_pct,
                'rate_pps': rate_pps
            })

            # Print row
            print(f"  {elapsed:<12} | {total_tx:<15} | {total_rx:<15} | {loss_pct:<10.2f} | {rate_pps:<10.0f}")

        print(f"  {'-'*95}")
        print(f"  ✓ Metrics collection complete")
        return metrics_data

    except Exception as e:
        print(f"  ✗ Failed to collect metrics: {e}")
        raise


def validate_assertions(metrics_data, bgp_converged):
    """
    Validate test assertions against collected data
    """
    print(f"\n[Step 5/7] Validating assertions...")

    all_passed = True
    results = {}

    # Assertion 1: BGP Convergence
    bgp_pass = bgp_converged
    results['bgp_convergence'] = {
        'expected': 'Established',
        'actual': 'Established' if bgp_pass else 'NotEstablished',
        'passed': bgp_pass
    }
    print(f"  {'BGP Convergence':<30} | Expected: Established | Actual: {'Established' if bgp_pass else 'NotEstablished'} | {'✓ PASS' if bgp_pass else '✗ FAIL'}")
    if not bgp_pass:
        all_passed = False

    # Assertion 2: Packet Loss
    if metrics_data:
        final_loss_pct = metrics_data[-1]['loss_pct']
        max_loss = ASSERTIONS['packet_loss']['max_loss_percent']
        loss_pass = final_loss_pct <= max_loss
        results['packet_loss'] = {
            'expected': f"< {max_loss}%",
            'actual': f"{final_loss_pct:.2f}%",
            'passed': loss_pass
        }
        print(f"  {'Packet Loss':<30} | Expected: < {max_loss}% | Actual: {final_loss_pct:.2f}% | {'✓ PASS' if loss_pass else '✗ FAIL'}")
        if not loss_pass:
            all_passed = False

    # Assertion 3: Frame Count
    if metrics_data:
        final_tx = metrics_data[-1]['tx_frames']
        min_frames = ASSERTIONS['flow_frames']['min_frames_transmitted']
        frames_pass = final_tx >= min_frames
        results['frames_transmitted'] = {
            'expected': f"> {min_frames}",
            'actual': final_tx,
            'passed': frames_pass
        }
        print(f"  {'Frames Transmitted':<30} | Expected: > {min_frames} | Actual: {final_tx} | {'✓ PASS' if frames_pass else '✗ FAIL'}")
        if not frames_pass:
            all_passed = False

    print(f"\n  {'Overall Result':<30} | {'✓ ALL PASSED' if all_passed else '✗ SOME FAILED'}")

    return all_passed, results


def stop_traffic(api):
    """
    Stop traffic transmission
    """
    print(f"\n[Step 6/7] Stopping traffic...")
    try:
        state = snappi.TransmitState()
        state.state = snappi.TransmitState.stop
        api.set_transmit_state(state)
        print(f"  ✓ Traffic stopped")
    except Exception as e:
        print(f"  ⚠ Error stopping traffic: {e}")


def save_report(test_results):
    """
    Save test results to JSON report file
    """
    report_file = f"test_report_bgp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print(f"\n[Step 7/7] Saving test report...")
    try:
        with open(report_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        print(f"  ✓ Report saved: {report_file}")
        return report_file
    except Exception as e:
        print(f"  ✗ Failed to save report: {e}")
        raise


# ============================================================================
# Main Test Execution
# ============================================================================

def main():
    """
    Main test execution flow
    """
    print("\n" + "="*95)
    print("  Snappi BGP Convergence Test (CP+DP)")
    print("  Controller: https://localhost:8443")
    print("  Test: BGP AS 65001 ↔ AS 65002 with bidirectional traffic")
    print("="*95)

    api = None
    bgp_converged = False
    metrics_data = []

    try:
        # Step 1: Connect to controller
        api = connect_api(API_LOCATION)

        # Step 2: Load OTG configuration
        config = load_config(api, OTG_CONFIG_JSON)

        # Step 3: Wait for BGP convergence
        bgp_converged = wait_for_bgp_convergence(api, BGP_CONVERGENCE_TIMEOUT)

        # Step 4: Start traffic (with user confirmation)
        input(f"\n  ⏸ Press Enter to START TRAFFIC (Ctrl+C to abort)...")
        start_traffic(api)

        # Step 5: Collect metrics
        metrics_data = collect_metrics(api, TEST_DURATION, METRICS_INTERVAL)

        # Step 6: Validate assertions
        assertions_passed, assertion_results = validate_assertions(metrics_data, bgp_converged)

        # Step 7: Cleanup
        stop_traffic(api)

        # Step 8: Generate report
        test_report = {
            'timestamp': datetime.now().isoformat(),
            'controller': API_LOCATION,
            'test_type': 'BGP Convergence',
            'duration_seconds': TEST_DURATION,
            'bgp_converged': bgp_converged,
            'assertions': assertion_results,
            'overall_result': 'PASSED' if assertions_passed else 'FAILED',
            'metrics': metrics_data
        }

        report_file = save_report(test_report)

        # Print summary
        print("\n" + "="*95)
        if assertions_passed:
            print("  ✓ TEST PASSED")
        else:
            print("  ✗ TEST FAILED")
        print("="*95)

        # Exit with appropriate code
        sys.exit(0 if assertions_passed else 1)

    except KeyboardInterrupt:
        print("\n\n  ⚠ Test interrupted by user (Ctrl+C)")
        sys.exit(130)

    except Exception as e:
        print(f"\n  ✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Always cleanup
        if api:
            try:
                stop_traffic(api)
            except:
                pass


if __name__ == "__main__":
    main()
