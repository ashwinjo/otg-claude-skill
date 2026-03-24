#!/usr/bin/env python3
"""
B2B Dataplane 1500-byte Jumbo Frame Test
=========================================
Test Name  : B2B Dataplane 1500-byte Jumbo Frame Test
Generated  : 2026-03-23
OTG Config : b2b_dataplane_1500bytes.json (embedded)
Controller : https://localhost:8443

Topology
--------
  port1 (localhost:5555) <---B2B---> port2 (localhost:5556)

Flows
-----
  port1_to_port2 : port1 TX -> port2 RX  @ 100% line rate, 1500-byte Eth/IPv4, continuous
  port2_to_port1 : port2 TX -> port1 RX  @ 100% line rate, 1500-byte Eth/IPv4, continuous

Layer 1
-------
  Speed          : 10 Gbps
  Auto-negotiate : disabled

Test Execution Flow
-------------------
  1. Connect to controller with retry (exponential backoff, 3 attempts)
  2. Push embedded OTG config (no latency/loss metric fields -- ixia-c-one compatible)
  3. Start all flows via set_control_state
  4. Stream flow + port metrics every 1 s for 60 s
  5. Stop traffic via set_control_state (programmatic stop, not duration-based)
  6. Brief settle delay, then collect final metrics snapshot
  7. Run assertions on final snapshot:
       port1_to_port2: frames_tx > 0, frames_rx > 0, loss_pct < 0.1%, throughput_mbps > 0
       port2_to_port1: frames_tx > 0, frames_rx > 0, loss_pct < 0.1%, throughput_mbps > 0
       bidirectional: both flows have frames_rx > 0
  8. Print final throughput summary table
  9. Write JSON report to test_b2b_dataplane_1500bytes_report_<timestamp>.json
 10. Exit 0 on PASS, 1 on FAIL

Usage
-----
  pip install snappi
  python test_b2b_dataplane_1500bytes.py

Exit Codes
----------
  0  All assertions passed
  1  Assertion failure or unrecoverable error

Notes on ixia-c-one compatibility
-----------------------------------
  - No latency metrics in OTG config (unsupported; see fixes.md)
  - No loss metrics in OTG config (unsupported on ixia-c-one)
  - Duration kept as "continuous" (fixed_seconds crashes keng-controller; see fixes.md)
  - Traffic stopped programmatically via set_control_state after 60 s
  - cfg.deserialize() used, NOT cfg.loads() (see fixes.md: Config.loads() Does Not Exist)
  - ControlState uses cs.traffic.flow_transmit.state string, not snappi.ControlState.Protocol pattern
  - Rate uses "choice": "percentage", "percentage": 100 (NOT "choice": "line" -- invalid enum value)

Throughput calculation
----------------------
  Wire frame size = 1500 (payload) + 20 (preamble + SFD + IFG) = 1520 bytes
  RX Mbps = (frames * 1520 * 8) / duration_s / 1_000_000
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
# Suppress TLS warnings -- self-signed certificate is expected on ixia-c Docker
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
log = logging.getLogger("b2b_dataplane_1500bytes")

# ===========================================================================
# EMBEDDED CONFIGURATION
# All infrastructure details embedded -- no external files required.
# ===========================================================================

CONTROLLER_URL: str = "https://localhost:8443"
VERIFY_TLS: bool = False          # self-signed cert; set True + CA path in production

TEST_NAME: str = "B2B Dataplane 1500-byte Jumbo Frame Test"
TEST_DURATION_S: int = 60         # run traffic for 60 s, then stop programmatically
METRICS_INTERVAL_S: int = 1       # print live stats every 1 s

# Assertion thresholds
LOSS_TOLERANCE_PCT: float = 0.1   # allow up to 0.1% frame loss

# Throughput calculation
# 1500-byte payload + 20-byte Ethernet overhead (preamble 7 + SFD 1 + IFG 12)
FRAME_SIZE_BYTES: int = 1500
WIRE_OVERHEAD_BYTES: int = 20
WIRE_FRAME_BYTES: int = FRAME_SIZE_BYTES + WIRE_OVERHEAD_BYTES   # 1520 bytes on wire
LINK_SPEED_GBPS: float = 10.0

# OTG Configuration -- derived from b2b_dataplane_1500bytes.json
#
# Compatibility adjustments applied before embedding:
#   - No latency/loss metric fields (unsupported on ixia-c-one)
#   - Duration kept as "continuous" (fixed_seconds crashes keng-controller)
#   - metrics.enable = true (required for flow counter collection)
#   - Rate: "choice": "percentage", "percentage": 100
#     NOT "choice": "line" -- "line" is not a valid OTG rate choice enum value;
#     the corrected source config b2b_dataplane_1500bytes.json uses "percentage": 100
OTG_CONFIG_JSON: str = r"""
{
  "ports": [
    {
      "name": "port1",
      "location": "localhost:5555"
    },
    {
      "name": "port2",
      "location": "localhost:5556"
    }
  ],
  "layer1": [
    {
      "name": "layer1_settings",
      "port_names": ["port1", "port2"],
      "speed": "speed_10_gbps",
      "auto_negotiate": false,
      "ieee_media_defaults": false
    }
  ],
  "flows": [
    {
      "name": "port1_to_port2",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "port1",
          "rx_names": ["port2"]
        }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "dst": {
              "choice": "value",
              "value": "00:00:00:00:00:02"
            },
            "src": {
              "choice": "value",
              "value": "00:00:00:00:00:01"
            }
          }
        },
        {
          "choice": "ipv4",
          "ipv4": {
            "src": {
              "choice": "value",
              "value": "192.168.1.1"
            },
            "dst": {
              "choice": "value",
              "value": "192.168.2.1"
            }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 1500
      },
      "rate": {
        "choice": "percentage",
        "percentage": 100
      },
      "duration": {
        "choice": "continuous"
      },
      "metrics": {
        "enable": true
      }
    },
    {
      "name": "port2_to_port1",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "port2",
          "rx_names": ["port1"]
        }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "dst": {
              "choice": "value",
              "value": "00:00:00:00:00:01"
            },
            "src": {
              "choice": "value",
              "value": "00:00:00:00:00:02"
            }
          }
        },
        {
          "choice": "ipv4",
          "ipv4": {
            "src": {
              "choice": "value",
              "value": "192.168.2.1"
            },
            "dst": {
              "choice": "value",
              "value": "192.168.1.1"
            }
          }
        }
      ],
      "size": {
        "choice": "fixed",
        "fixed": 1500
      },
      "rate": {
        "choice": "percentage",
        "percentage": 100
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
    """Connect to the OTG controller with exponential-backoff retry.

    Attempts: 1 s, 2 s, 4 s wait between retries.
    Probes connectivity by calling api.get_config() -- fails fast if unreachable.
    """
    for attempt in range(1, max_retries + 1):
        try:
            log.info(
                "Connecting to %s (attempt %d/%d)...", url, attempt, max_retries
            )
            api = snappi.api(location=url, verify=VERIFY_TLS)
            # Connectivity probe -- raises immediately if controller is unreachable
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
                log.error(
                    "Could not connect to controller at %s after %d attempts.",
                    url,
                    max_retries,
                )
                log.error(
                    "Verify ixia-c is running: docker ps | grep keng-controller"
                )
                raise


def _push_config(api: snappi.Api) -> snappi.Config:
    """Deserialise the embedded OTG JSON and push it to the controller.

    Uses cfg.deserialize() -- NOT cfg.loads() (which does not exist on
    snappi.Config; see fixes.md: Config.loads() Does Not Exist).
    """
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
    """Start all configured flows via set_control_state."""
    log.info("Starting traffic (all flows, 100%% line rate, 1500-byte frames)...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("Traffic started.")


def _stop_traffic(api: snappi.Api) -> None:
    """Stop all flows programmatically via set_control_state.

    Continuous-duration flows must be stopped this way.
    fixed_seconds is deliberately NOT used -- it causes keng-controller to
    crash-restart on ixia-c-one, dropping the API connection mid-test.
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


def _clear_config(api: snappi.Api) -> None:
    """Push an empty config to release resources on the controller."""
    log.info("Clearing config on controller...")
    try:
        api.set_config(snappi.Config())
        log.info("Config cleared.")
    except Exception as exc:
        log.warning("Error clearing config (non-fatal): %s", exc)


# ===========================================================================
# THROUGHPUT HELPERS
# ===========================================================================


def _frames_to_mbps(frames: int, duration_s: float) -> float:
    """Convert frame count + duration to throughput in Mbps (wire rate).

    Uses 1500-byte payload + 20-byte Ethernet overhead = 1520 bytes per wire frame.
    """
    if duration_s <= 0:
        return 0.0
    bits_on_wire = frames * WIRE_FRAME_BYTES * 8
    return bits_on_wire / duration_s / 1_000_000


def _frames_to_gbps(frames: int, duration_s: float) -> float:
    """Convert frame count + duration to throughput in Gbps (wire rate)."""
    return _frames_to_mbps(frames, duration_s) / 1000


def _line_rate_pct(gbps: float, link_gbps: float = LINK_SPEED_GBPS) -> float:
    """Return percentage of link speed utilisation."""
    if link_gbps <= 0:
        return 0.0
    return (gbps / link_gbps) * 100.0


# ===========================================================================
# METRICS COLLECTION
# ===========================================================================


def _get_flow_metrics(api: snappi.Api) -> list[Any]:
    """Return raw flow_metrics list from a FLOW metrics request.

    Uses req.choice = req.FLOW -- the fabricated req.flow.state pattern
    does not exist (see fixes.md: Fabricated Metrics API).
    """
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
    """Poll flow and port metrics every *interval_s* seconds for *duration_s* seconds.

    Prints a live table to stdout at each interval -- output is unbuffered
    so stats are visible in real-time during execution.
    Returns a list of per-interval metric snapshots for the JSON report.
    Traffic start/stop is managed by the caller.
    """
    snapshots: list[dict[str, Any]] = []
    end_time = time.monotonic() + duration_s
    snapshot_num = 0
    prev_rx: dict[str, int] = {}   # track previous RX frame count for instantaneous rate

    # Table header
    header = (
        f"{'t(s)':>5s}  "
        f"{'Flow':<20s}  "
        f"{'TX Frames':>12s}  "
        f"{'RX Frames':>12s}  "
        f"{'Lost':>8s}  "
        f"{'Loss%':>7s}  "
        f"{'RX Mbps':>10s}  "
        f"{'Line%':>7s}"
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

                # Instantaneous RX rate over this polling window
                delta_rx = rx - prev_rx.get(fm.name, 0)
                prev_rx[fm.name] = rx
                rx_mbps = _frames_to_mbps(delta_rx, interval_s)
                line_pct = _line_rate_pct(rx_mbps / 1000)

                flow_data[fm.name] = {
                    "frames_tx": tx,
                    "frames_rx": rx,
                    "frames_lost": lost,
                    "loss_pct": round(loss_pct, 6),
                    "rx_mbps_instant": round(rx_mbps, 2),
                    "line_pct_instant": round(line_pct, 2),
                }

                print(
                    f"{elapsed:>5d}  "
                    f"{fm.name:<20s}  "
                    f"{tx:>12d}  "
                    f"{rx:>12d}  "
                    f"{lost:>8d}  "
                    f"{loss_pct:>7.4f}  "
                    f"{rx_mbps:>10.2f}  "
                    f"{line_pct:>7.2f}"
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
                    # field name varies by controller version -- try both
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
            rx_mbps = _frames_to_mbps(rx, TEST_DURATION_S)
            rx_gbps = rx_mbps / 1000
            line_pct = _line_rate_pct(rx_gbps)

            result["flows"][fm.name] = {
                "frames_tx": tx,
                "frames_rx": rx,
                "frames_lost": lost,
                "loss_pct": round(loss_pct, 6),
                "throughput_fps": round(rx / TEST_DURATION_S, 2) if TEST_DURATION_S > 0 else 0.0,
                "throughput_mbps": round(rx_mbps, 2),
                "throughput_gbps": round(rx_gbps, 4),
                "line_rate_pct": round(line_pct, 2),
            }
    except Exception as exc:
        log.warning("Could not collect final flow metrics: %s", exc)

    try:
        for pm in _get_port_metrics(api):
            tx = int(pm.frames_tx)
            rx = int(pm.frames_rx)
            bytes_tx = int(pm.bytes_tx)
            bytes_rx = int(pm.bytes_rx)
            tx_mbps = (bytes_tx * 8) / TEST_DURATION_S / 1_000_000 if TEST_DURATION_S > 0 else 0.0
            rx_mbps = (bytes_rx * 8) / TEST_DURATION_S / 1_000_000 if TEST_DURATION_S > 0 else 0.0

            result["ports"][pm.name] = {
                "frames_tx": tx,
                "frames_rx": rx,
                "bytes_tx": bytes_tx,
                "bytes_rx": bytes_rx,
                "tx_mbps": round(tx_mbps, 2),
                "rx_mbps": round(rx_mbps, 2),
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

    Per flow (port1_to_port2, port2_to_port1):
      1. frames_tx > 0           (traffic was actually sent)
      2. frames_rx > 0           (traffic was actually received)
      3. loss_pct < 0.1%         (max 0.1% frame loss tolerance)
      4. throughput_mbps > 0     (non-zero measured throughput)

    Bidirectional:
      5. Both flows must have frames_rx > 0 (traffic flowing in both directions)

    Returns (all_passed, list_of_assertion_results).
    """
    results: list[dict[str, Any]] = []
    all_passed = True
    flows = final_metrics.get("flows", {})

    # ------------------------------------------------------------------
    # Per-flow assertions
    # ------------------------------------------------------------------
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
        loss_pct: float = fm["loss_pct"]
        throughput_mbps: float = fm["throughput_mbps"]

        checks: list[dict[str, Any]] = [
            {
                "assertion": f"{flow_name}: frames_tx > 0 (traffic was sent)",
                "flow": flow_name,
                "metric": "frames_tx",
                "expected": "> 0",
                "actual": tx,
                "passed": tx > 0,
            },
            {
                "assertion": f"{flow_name}: frames_rx > 0 (traffic was received)",
                "flow": flow_name,
                "metric": "frames_rx",
                "expected": "> 0",
                "actual": rx,
                "passed": rx > 0,
            },
            {
                "assertion": (
                    f"{flow_name}: loss_pct < {LOSS_TOLERANCE_PCT}%"
                    f" (max {LOSS_TOLERANCE_PCT}% tolerance)"
                ),
                "flow": flow_name,
                "metric": "loss_pct",
                "expected": f"< {LOSS_TOLERANCE_PCT}",
                "actual": loss_pct,
                "frames_lost": fm["frames_lost"],
                "passed": (tx == 0) or (loss_pct < LOSS_TOLERANCE_PCT),
            },
            {
                "assertion": f"{flow_name}: throughput_mbps > 0 (non-zero RX rate)",
                "flow": flow_name,
                "metric": "throughput_mbps",
                "expected": "> 0",
                "actual": throughput_mbps,
                "throughput_gbps": fm["throughput_gbps"],
                "line_rate_pct": fm["line_rate_pct"],
                "passed": throughput_mbps > 0,
            },
        ]

        for check in checks:
            status = "PASS" if check["passed"] else "FAIL"
            log.info(
                "[%s] %s  (actual: %s)", status, check["assertion"], check["actual"]
            )
            if not check["passed"]:
                all_passed = False
            results.append(check)

    # ------------------------------------------------------------------
    # Bidirectional assertion -- both flows must have received frames
    # ------------------------------------------------------------------
    both_rx = all(
        flows.get(fn, {}).get("frames_rx", 0) > 0
        for fn in flow_names
        if fn in flows
    )
    bidi_check: dict[str, Any] = {
        "assertion": "bidirectional: both flows have frames_rx > 0",
        "flows": flow_names,
        "metric": "frames_rx",
        "expected": "> 0 on all flows",
        "actual": {fn: flows.get(fn, {}).get("frames_rx", 0) for fn in flow_names},
        "passed": both_rx,
    }
    status = "PASS" if both_rx else "FAIL"
    log.info("[%s] %s", status, bidi_check["assertion"])
    if not both_rx:
        all_passed = False
    results.append(bidi_check)

    return all_passed, results


# ===========================================================================
# REPORT & SUMMARY
# ===========================================================================


def _print_throughput_summary(final_metrics: dict[str, Any]) -> None:
    """Print a human-readable throughput summary table to stdout."""
    flows = final_metrics.get("flows", {})
    if not flows:
        return

    print()
    print("=" * 78)
    print("  THROUGHPUT SUMMARY  (1500-byte frames, 10 Gbps link)")
    print("=" * 78)
    print(
        f"  {'Flow':<22s}  "
        f"{'TX Frames':>12s}  "
        f"{'RX Frames':>12s}  "
        f"{'Loss%':>8s}  "
        f"{'RX Mbps':>10s}  "
        f"{'RX Gbps':>10s}  "
        f"{'Line%':>7s}"
    )
    print("  " + "-" * 74)
    for flow_name, fm in flows.items():
        print(
            f"  {flow_name:<22s}  "
            f"{fm['frames_tx']:>12d}  "
            f"{fm['frames_rx']:>12d}  "
            f"{fm['loss_pct']:>8.4f}  "
            f"{fm['throughput_mbps']:>10.2f}  "
            f"{fm['throughput_gbps']:>10.4f}  "
            f"{fm['line_rate_pct']:>7.2f}"
        )
    print("=" * 78)
    print()


def _save_report(data: dict[str, Any]) -> str:
    """Write the test report to a timestamped JSON file. Returns the file path."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = f"test_b2b_dataplane_1500bytes_report_{ts}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    log.info("Report written to %s", path)
    return path


# ===========================================================================
# MAIN TEST EXECUTION
# ===========================================================================


def run_test() -> bool:
    """Execute the B2B 1500-byte dataplane test. Returns True if all assertions pass."""
    log.info("=" * 70)
    log.info("Test       : %s", TEST_NAME)
    log.info("Controller : %s", CONTROLLER_URL)
    log.info("Port map   : port1=localhost:5555  |  port2=localhost:5556")
    log.info("Speed      : %s Gbps  |  auto-negotiate=off", LINK_SPEED_GBPS)
    log.info(
        "Flows      : port1_to_port2 + port2_to_port1  |  100%% line rate  |  1500-byte  |  %d s",
        TEST_DURATION_S,
    )
    log.info("Wire frame : %d bytes (1500 payload + %d overhead)", WIRE_FRAME_BYTES, WIRE_OVERHEAD_BYTES)
    log.info("=" * 70)

    started_at = datetime.now(tz=timezone.utc).isoformat()
    api: snappi.Api | None = None
    traffic_started: bool = False
    overall_passed: bool = False
    metric_snapshots: list[dict[str, Any]] = []
    final_metrics: dict[str, Any] = {}
    assertion_results: list[dict[str, Any]] = []
    error_msg: str | None = None

    # Flow names must match the embedded OTG config exactly
    flow_names: list[str] = ["port1_to_port2", "port2_to_port1"]

    try:
        # ------------------------------------------------------------------
        # Step 1: Connect to controller
        # ------------------------------------------------------------------
        api = _connect(CONTROLLER_URL)

        # ------------------------------------------------------------------
        # Step 2: Push OTG config
        # ------------------------------------------------------------------
        _push_config(api)

        # ------------------------------------------------------------------
        # Step 3: Start all flows
        # No devices or protocols in this config -- pure dataplane B2B test.
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

        # Brief pause for controller to settle final counters before reading
        time.sleep(1)

        # ------------------------------------------------------------------
        # Step 6: Collect final metrics snapshot
        # ------------------------------------------------------------------
        log.info("Collecting final metrics snapshot...")
        final_metrics = _collect_final_metrics(api)

        # Log per-flow summary
        for name, fm in final_metrics.get("flows", {}).items():
            log.info(
                "  [%s]  tx=%d  rx=%d  lost=%d  loss=%.6f%%  "
                "%.2f Mbps  %.4f Gbps  %.2f%% line",
                name,
                fm["frames_tx"],
                fm["frames_rx"],
                fm["frames_lost"],
                fm["loss_pct"],
                fm["throughput_mbps"],
                fm["throughput_gbps"],
                fm["line_rate_pct"],
            )

        # ------------------------------------------------------------------
        # Step 7: Run assertions
        # ------------------------------------------------------------------
        log.info("-" * 70)
        log.info("Validating assertions...")
        overall_passed, assertion_results = _run_assertions(final_metrics, flow_names)

        # ------------------------------------------------------------------
        # Step 8: Print throughput summary table
        # ------------------------------------------------------------------
        _print_throughput_summary(final_metrics)

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
        # Always stop traffic -- even on exception or keyboard interrupt
        if api is not None and traffic_started:
            _stop_traffic(api)

        # Always clear config on exit to release traffic engine resources
        if api is not None:
            _clear_config(api)

    # -----------------------------------------------------------------------
    # Step 9: Write JSON report -- always written, pass or fail
    # -----------------------------------------------------------------------
    finished_at = datetime.now(tz=timezone.utc).isoformat()

    report: dict[str, Any] = {
        "test_name": TEST_NAME,
        "controller": CONTROLLER_URL,
        "port_mapping": {
            "port1": "localhost:5555",
            "port2": "localhost:5556",
        },
        "layer1": {
            "speed": "speed_10_gbps",
            "auto_negotiate": False,
            "ieee_media_defaults": False,
        },
        "flows": flow_names,
        "frame_size_bytes": FRAME_SIZE_BYTES,
        "wire_frame_bytes": WIRE_FRAME_BYTES,
        "link_speed_gbps": LINK_SPEED_GBPS,
        "started_at": started_at,
        "finished_at": finished_at,
        "test_duration_s": TEST_DURATION_S,
        "metrics_interval_s": METRICS_INTERVAL_S,
        "loss_tolerance_pct": LOSS_TOLERANCE_PCT,
        "overall_passed": overall_passed,
        "verdict": "PASSED" if overall_passed else "FAILED",
        "error": error_msg,
        "assertions": assertion_results,
        "final_metrics": final_metrics,
        "metric_snapshots": metric_snapshots,
    }
    report_path = _save_report(report)
    print(f"\nReport : {report_path}")
    print(f"Result : {'PASSED' if overall_passed else 'FAILED'}")

    return overall_passed


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
