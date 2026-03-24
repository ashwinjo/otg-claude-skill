#!/usr/bin/env python3
"""
B2B Loopback Test — ixia-c-one (Containerlab)
==============================================
Generated  : 2026-03-22
OTG Config : b2b_loopback_clab.json (embedded)
Controller : https://172.20.20.2:8443

Topology
--------
  P1 (eth1) <----loopback----> P2 (eth2)

Flows
-----
  P1_to_P2 : eth1 TX  ->  eth2 RX  @ 1 000 pps, 64-byte Ethernet frames, continuous
  P2_to_P1 : eth2 TX  ->  eth1 RX  @ 1 000 pps, 64-byte Ethernet frames, continuous

ixia-c-one compatibility notes
-------------------------------
  - No latency / loss metrics in OTG config (unsupported on ixia-c-one)
  - No fixed_seconds duration (crashes keng-controller; see fixes.md)
  - No options.port_options block (not required for Containerlab veth ports)
  - Pure Ethernet frames only — no IPv4/UDP headers in this loopback test
  - Traffic stopped programmatically via set_control_state after 30 s

Test Flow
---------
  1. Connect to controller (3 retries, exponential backoff)
  2. Push embedded OTG config
  3. Start all flows
  4. Stream port + flow metrics every 5 s for 30 s
  5. Stop traffic via set_control_state (programmatic stop, not duration-based)
  6. Collect final metrics snapshot
  7. Assert on both flows:
       frames_tx > 0           (traffic was sent)
       frames_rx > 0           (traffic was received)
       frames_tx == frames_rx  (zero loss — loopback must be lossless)
  8. Calculate throughput: frames_rx / 30 s = frames per second
  9. Write JSON report to test_report_<timestamp>.json

Usage
-----
  pip install snappi
  python test_b2b_loopback_clab.py

Exit codes
----------
  0  All assertions passed
  1  Assertion failure or unrecoverable error
"""

from __future__ import annotations

import json
import logging
import sys
import time
import urllib3
from datetime import datetime, timezone
from typing import Any

import snappi

# ---------------------------------------------------------------------------
# Suppress TLS warnings — self-signed certificate is expected on ixia-c-one
# ---------------------------------------------------------------------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("b2b_loopback_clab")

# ===========================================================================
# EMBEDDED CONFIGURATION
# All infrastructure details are embedded here — no external files required.
# ===========================================================================

CONTROLLER_URL: str = "https://172.20.20.2:8443"
VERIFY_TLS: bool = False            # self-signed cert; set True + CA path for production

TEST_NAME: str = "b2b_loopback_clab"
TEST_DURATION_S: int = 30           # run traffic for 30 s, then stop programmatically
METRICS_INTERVAL_S: int = 5         # print live stats every 5 s

# Port mapping (Containerlab veth pairs)
#   P1 -> eth1  (TX port)
#   P2 -> eth2  (RX port)

# OTG Configuration — verbatim from b2b_loopback_clab.json
# ixia-c-one compatible:
#   - no latency / loss metrics fields
#   - continuous duration (fixed_seconds crashes keng-controller — see fixes.md)
#   - pure Ethernet frames, no IPv4/UDP overlay
#   - metrics.enable = true (required for flow counter collection)
OTG_CONFIG_JSON: str = r"""
{
  "ports": [
    { "name": "P1", "location": "eth1" },
    { "name": "P2", "location": "eth2" }
  ],
  "flows": [
    {
      "name": "P1_to_P2",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "P1",
          "rx_names": ["P2"]
        }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "dst": { "choice": "value", "value": "00:00:00:00:00:02" },
            "src": { "choice": "value", "value": "00:00:00:00:00:01" }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 64
      },
      "rate": {
        "choice": "pps",
        "pps": 1000
      },
      "duration": {
        "choice": "continuous"
      },
      "metrics": {
        "enable": true
      }
    },
    {
      "name": "P2_to_P1",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "P2",
          "rx_names": ["P1"]
        }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "dst": { "choice": "value", "value": "00:00:00:00:00:01" },
            "src": { "choice": "value", "value": "00:00:00:00:00:02" }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 64
      },
      "rate": {
        "choice": "pps",
        "pps": 1000
      },
      "duration": {
        "choice": "continuous"
      },
      "metrics": {
        "enable": true
      }
    }
  ]
}
"""

# ===========================================================================
# CONNECTION & CONFIG HELPERS
# ===========================================================================


def _connect(url: str, max_retries: int = 3) -> snappi.Api:
    """Connect to the OTG controller with exponential-backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            log.info(
                "Connecting to %s (attempt %d/%d)...", url, attempt, max_retries
            )
            api = snappi.api(location=url, verify=VERIFY_TLS)
            # Validate connectivity — fetching config will fail fast if unreachable
            api.get_config()
            log.info("Connected successfully.")
            return api
        except Exception as exc:
            if attempt < max_retries:
                wait = 2 ** (attempt - 1)   # 1 s, 2 s, 4 s
                log.warning(
                    "Connection failed (%s). Retrying in %d s...", exc, wait
                )
                time.sleep(wait)
            else:
                log.error("Could not connect after %d attempts.", max_retries)
                raise


def _push_config(api: snappi.Api) -> snappi.Config:
    """Deserialise the embedded OTG JSON and push it to the controller."""
    log.info("Pushing OTG configuration...")
    cfg = snappi.Config()
    cfg.deserialize(OTG_CONFIG_JSON)
    api.set_config(cfg)
    log.info(
        "Config pushed: %d port(s), %d flow(s).",
        len(cfg.ports),
        len(cfg.flows),
    )
    return cfg


# ===========================================================================
# TRAFFIC CONTROL
# ===========================================================================


def _start_traffic(api: snappi.Api) -> None:
    """Start all configured flows."""
    log.info("Starting traffic (all flows)...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("Traffic started.")


def _stop_traffic(api: snappi.Api) -> None:
    """Stop all flows programmatically via set_control_state.

    This is the required stop method for continuous-duration flows.
    fixed_seconds duration is deliberately NOT used — it causes keng-controller
    to crash-restart on ixia-c-one, dropping the API connection mid-test.
    (See fixes.md: fixed_seconds crashes controller)
    """
    log.info("Stopping traffic...")
    try:
        cs = snappi.ControlState()
        cs.traffic.flow_transmit.state = "stop"
        api.set_control_state(cs)
        log.info("Traffic stopped.")
    except Exception as exc:
        log.warning("Error stopping traffic (non-fatal): %s", exc)


# ===========================================================================
# METRICS COLLECTION
# ===========================================================================


def _get_flow_metrics(api: snappi.Api) -> list[Any]:
    """Return raw flow_metrics list from a FLOW metrics request."""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    return api.get_metrics(req).flow_metrics


def _get_port_metrics(api: snappi.Api) -> list[Any]:
    """Return raw port_metrics list from a PORT metrics request."""
    req = snappi.MetricsRequest()
    req.choice = req.PORT
    return api.get_metrics(req).port_metrics


def _poll_metrics(
    api: snappi.Api,
    duration_s: int,
    interval_s: int,
) -> list[dict[str, Any]]:
    """Poll flow and port metrics every *interval_s* s for *duration_s* s.

    Prints a live table to stdout every interval.
    Returns a list of per-interval snapshots for the JSON report.
    Traffic lifecycle (start/stop) is managed by the caller.
    """
    snapshots: list[dict[str, Any]] = []
    end_time = time.monotonic() + duration_s
    snapshot_num = 0

    # Print table header
    header = (
        f"{'Elapsed':>8s}  "
        f"{'Flow':<14s}  "
        f"{'TX Frames':>12s}  "
        f"{'RX Frames':>12s}  "
        f"{'Loss':>8s}  "
        f"{'RX pps':>10s}"
    )
    sep = "-" * len(header)
    print()
    print(header)
    print(sep)

    while time.monotonic() < end_time:
        sleep_for = min(interval_s, max(0.0, end_time - time.monotonic()))
        time.sleep(sleep_for)

        snapshot_num += 1
        elapsed = int(duration_s - max(0.0, end_time - time.monotonic()))

        flow_data: dict[str, Any] = {}
        try:
            for fm in _get_flow_metrics(api):
                tx = int(fm.frames_tx)
                rx = int(fm.frames_rx)
                lost = tx - rx
                loss_pct = (lost / tx * 100.0) if tx > 0 else 0.0
                # Instantaneous RX rate over this polling interval
                rx_pps = rx / interval_s if interval_s > 0 else 0.0

                flow_data[fm.name] = {
                    "frames_tx": tx,
                    "frames_rx": rx,
                    "frames_lost": lost,
                    "loss_pct": round(loss_pct, 6),
                    "rx_pps": round(rx_pps, 1),
                }

                print(
                    f"{elapsed:>8d}  "
                    f"{fm.name:<14s}  "
                    f"{tx:>12d}  "
                    f"{rx:>12d}  "
                    f"{lost:>8d}  "
                    f"{rx_pps:>10.1f}"
                )
        except Exception as exc:
            log.warning("Could not fetch flow metrics at t=%d s: %s", elapsed, exc)

        port_data: dict[str, Any] = {}
        try:
            for pm in _get_port_metrics(api):
                port_data[pm.name] = {
                    "frames_tx": int(pm.frames_tx),
                    "frames_rx": int(pm.frames_rx),
                    "bytes_tx": int(pm.bytes_tx),
                    "bytes_rx": int(pm.bytes_rx),
                    # field name varies by controller version
                    "link_state": (
                        getattr(pm, "link", None)
                        or getattr(pm, "link_state", "unknown")
                    ),
                }
        except Exception as exc:
            log.warning("Could not fetch port metrics at t=%d s: %s", elapsed, exc)

        snapshots.append(
            {
                "snapshot": snapshot_num,
                "elapsed_s": elapsed,
                "flows": flow_data,
                "ports": port_data,
            }
        )

    print(sep)
    print()
    return snapshots


def _collect_final_metrics(api: snappi.Api) -> dict[str, Any]:
    """Pull one final snapshot of all flow and port metrics after traffic stops."""
    result: dict[str, Any] = {"flows": {}, "ports": {}}

    try:
        for fm in _get_flow_metrics(api):
            tx = int(fm.frames_tx)
            rx = int(fm.frames_rx)
            lost = tx - rx
            loss_pct = (lost / tx * 100.0) if tx > 0 else 0.0
            result["flows"][fm.name] = {
                "frames_tx": tx,
                "frames_rx": rx,
                "frames_lost": lost,
                "loss_pct": round(loss_pct, 6),
                # throughput = total frames received / test duration
                "throughput_fps": round(rx / TEST_DURATION_S, 2) if TEST_DURATION_S > 0 else 0.0,
            }
    except Exception as exc:
        log.warning("Could not collect final flow metrics: %s", exc)

    try:
        for pm in _get_port_metrics(api):
            result["ports"][pm.name] = {
                "frames_tx": int(pm.frames_tx),
                "frames_rx": int(pm.frames_rx),
                "bytes_tx": int(pm.bytes_tx),
                "bytes_rx": int(pm.bytes_rx),
                "link_state": (
                    getattr(pm, "link", None)
                    or getattr(pm, "link_state", "unknown")
                ),
            }
    except Exception as exc:
        log.warning("Could not collect final port metrics: %s", exc)

    return result


# ===========================================================================
# ASSERTIONS
# ===========================================================================


def _run_assertions(
    final_metrics: dict[str, Any],
    flow_names: list[str],
) -> tuple[bool, list[dict[str, Any]]]:
    """Validate all assertions against the final metric snapshot.

    Per flow (P1_to_P2, P2_to_P1):
      1. frames_tx > 0           (traffic was actually sent)
      2. frames_rx > 0           (traffic was actually received)
      3. frames_tx == frames_rx  (zero packet loss — loopback must be lossless)

    Returns (all_passed, list_of_assertion_results).
    """
    results: list[dict[str, Any]] = []
    all_passed = True

    flows = final_metrics.get("flows", {})

    for flow_name in flow_names:
        if flow_name not in flows:
            entry: dict[str, Any] = {
                "assertion": f"{flow_name}: flow found in metrics",
                "flow": flow_name,
                "passed": False,
                "error": "Flow not present in final metrics response",
            }
            log.error("[FAIL] %s: flow not found in metrics", flow_name)
            results.append(entry)
            all_passed = False
            continue

        fm = flows[flow_name]
        tx: int = fm["frames_tx"]
        rx: int = fm["frames_rx"]

        checks = [
            {
                "assertion": f"{flow_name}: frames_tx > 0",
                "flow": flow_name,
                "metric": "frames_tx",
                "expected": "> 0",
                "actual": tx,
                "passed": tx > 0,
            },
            {
                "assertion": f"{flow_name}: frames_rx > 0",
                "flow": flow_name,
                "metric": "frames_rx",
                "expected": "> 0",
                "actual": rx,
                "passed": rx > 0,
            },
            {
                "assertion": f"{flow_name}: frames_tx == frames_rx (zero loss)",
                "flow": flow_name,
                "metric": "loss",
                "expected": 0,
                "actual": fm["frames_lost"],
                "loss_pct": fm["loss_pct"],
                "passed": fm["frames_lost"] == 0 and tx > 0,
            },
        ]

        for check in checks:
            status = "PASS" if check["passed"] else "FAIL"
            log.info(
                "[%s] %s  (actual: %s)",
                status,
                check["assertion"],
                check["actual"],
            )
            if not check["passed"]:
                all_passed = False
            results.append(check)

    return all_passed, results


# ===========================================================================
# REPORT
# ===========================================================================


def _save_report(data: dict[str, Any]) -> str:
    """Write the test report to a timestamped JSON file. Returns the path."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = f"test_report_{ts}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    log.info("Report written to %s", path)
    return path


# ===========================================================================
# MAIN TEST EXECUTION
# ===========================================================================


def run_test() -> bool:
    """Execute the B2B loopback test. Returns True if all assertions pass."""
    log.info("=" * 70)
    log.info("Test       : %s", TEST_NAME)
    log.info("Controller : %s", CONTROLLER_URL)
    log.info("Port map   : P1=eth1 (TX/RX)  |  P2=eth2 (TX/RX)")
    log.info(
        "Flows      : P1_to_P2  +  P2_to_P1  |  1000 pps  |  64-byte  |  %d s",
        TEST_DURATION_S,
    )
    log.info("=" * 70)

    started_at = datetime.now(tz=timezone.utc).isoformat()
    api: snappi.Api | None = None
    traffic_started: bool = False
    overall_passed: bool = False
    metric_snapshots: list[dict[str, Any]] = []
    final_metrics: dict[str, Any] = {}
    assertion_results: list[dict[str, Any]] = []
    throughput: list[dict[str, Any]] = []
    error_msg: str | None = None

    # Flow names must match the OTG config exactly
    flow_names: list[str] = ["P1_to_P2", "P2_to_P1"]

    try:
        # ------------------------------------------------------------------
        # Step 1: Connect
        # ------------------------------------------------------------------
        api = _connect(CONTROLLER_URL)

        # ------------------------------------------------------------------
        # Step 2: Push OTG config
        # ------------------------------------------------------------------
        _push_config(api)

        # ------------------------------------------------------------------
        # Step 3: Start all flows
        # No devices or protocols — pure B2B loopback, traffic only.
        # ------------------------------------------------------------------
        _start_traffic(api)
        traffic_started = True

        # ------------------------------------------------------------------
        # Step 4: Stream live metrics for TEST_DURATION_S seconds
        # ------------------------------------------------------------------
        log.info(
            "Running for %d s, printing metrics every %d s...",
            TEST_DURATION_S,
            METRICS_INTERVAL_S,
        )
        metric_snapshots = _poll_metrics(
            api,
            duration_s=TEST_DURATION_S,
            interval_s=METRICS_INTERVAL_S,
        )

        # ------------------------------------------------------------------
        # Step 5: Stop traffic programmatically
        # ------------------------------------------------------------------
        _stop_traffic(api)
        traffic_started = False

        # Brief pause so the controller can settle final counters before
        # we read them; ixia-c-one may still be flushing pipeline state.
        time.sleep(1)

        # ------------------------------------------------------------------
        # Step 6: Collect final metrics
        # ------------------------------------------------------------------
        log.info("Collecting final metrics snapshot...")
        final_metrics = _collect_final_metrics(api)

        # Log per-flow summary
        for name, fm in final_metrics.get("flows", {}).items():
            log.info(
                "  [%s]  tx=%d  rx=%d  lost=%d  loss=%.6f%%  throughput=%.2f fps",
                name,
                fm["frames_tx"],
                fm["frames_rx"],
                fm["frames_lost"],
                fm["loss_pct"],
                fm["throughput_fps"],
            )

        # ------------------------------------------------------------------
        # Step 7: Assertions
        # ------------------------------------------------------------------
        log.info("-" * 70)
        log.info("Validating assertions...")
        overall_passed, assertion_results = _run_assertions(final_metrics, flow_names)

        # ------------------------------------------------------------------
        # Step 8: Throughput summary
        # ------------------------------------------------------------------
        for name, fm in final_metrics.get("flows", {}).items():
            throughput.append(
                {
                    "flow": name,
                    "frames_rx_total": fm["frames_rx"],
                    "test_duration_s": TEST_DURATION_S,
                    "throughput_fps": fm["throughput_fps"],
                }
            )
            log.info(
                "  Throughput [%s]: %d frames / %d s = %.2f fps",
                name,
                fm["frames_rx"],
                TEST_DURATION_S,
                fm["throughput_fps"],
            )

        verdict = "PASSED" if overall_passed else "FAILED"
        log.info("=" * 70)
        log.info("Test result: %s", verdict)
        log.info("=" * 70)

    except KeyboardInterrupt:
        log.warning("Test interrupted by user (Ctrl+C).")
        error_msg = "KeyboardInterrupt"
        overall_passed = False

    except Exception as exc:
        log.error("Unhandled error: %s", exc, exc_info=True)
        error_msg = str(exc)
        overall_passed = False

    finally:
        # Always stop traffic — even on exception or user interrupt
        if api is not None and traffic_started:
            _stop_traffic(api)

    # -----------------------------------------------------------------------
    # Write JSON report — always written, pass or fail
    # -----------------------------------------------------------------------
    finished_at = datetime.now(tz=timezone.utc).isoformat()

    report: dict[str, Any] = {
        "test_name": TEST_NAME,
        "controller": CONTROLLER_URL,
        "port_mapping": {"P1": "eth1", "P2": "eth2"},
        "flows": flow_names,
        "started_at": started_at,
        "finished_at": finished_at,
        "test_duration_s": TEST_DURATION_S,
        "metrics_interval_s": METRICS_INTERVAL_S,
        "overall_passed": overall_passed,
        "verdict": "PASSED" if overall_passed else "FAILED",
        "error": error_msg,
        "assertions": assertion_results,
        "throughput": throughput,
        "final_metrics": final_metrics,
        "metric_snapshots": metric_snapshots,
    }
    report_path = _save_report(report)
    print(f"\nReport: {report_path}")
    print(f"Result: {'PASSED' if overall_passed else 'FAILED'}")

    return overall_passed


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
