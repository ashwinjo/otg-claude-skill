#!/usr/bin/env python3
"""
BGP Convergence Test — Back-to-Back eBGP
=========================================
Generated  : 2026-03-22
OTG Config : bgp_convergence_cpdp.json (embedded)
Controller : https://localhost:8443

Topology
--------
  te1 (veth-a)                     te2 (veth-z)
  device_te1                       device_te2
  AS 65001 <--- eBGP session ---> AS 65002
  192.168.1.1                      192.168.1.2
  Advertises: 10.1.0.0/24          Advertises: 10.2.0.0/24

Test Flow
---------
  1. Push OTG config to controller
  2. Start protocols; poll until both eBGP sessions reach Established (timeout 60 s)
  3. Start bidirectional traffic at 1000 pps each direction
  4. Print flow + port metrics every 5 s for 120 s
  5. Stop traffic; stop protocols
  6. Assert: both BGP sessions Established on both peers
  7. Assert: packet loss < 0.1% on both flows
  8. Print PASS / FAIL summary
  9. Write JSON report to test_report_bgp_convergence.json

Usage
-----
  pip install snappi
  python test_bgp_convergence.py

Exit codes
----------
  0  All assertions passed
  1  One or more assertions failed or an unrecoverable error occurred
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
# Suppress TLS warnings for self-signed certificates (lab environment)
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
log = logging.getLogger("bgp_convergence")

# ===========================================================================
# EMBEDDED CONFIGURATION — all infrastructure details live here
# ===========================================================================

CONTROLLER_URL: str = "https://localhost:8443"
VERIFY_TLS: bool = False          # set True + supply CA bundle path for production

TEST_NAME: str = "bgp_convergence_cpdp"
METRICS_INTERVAL_S: int = 5
TEST_DURATION_S: int = 120
BGP_CONVERGENCE_TIMEOUT_S: int = 60
BGP_CONVERGENCE_POLL_S: int = 2

# Assertions
EXPECTED_BGP_SESSIONS: int = 2
MAX_LOSS_PCT: float = 0.1         # < 0.1 % packet loss threshold
FLOWS_UNDER_TEST: list[str] = ["flow_te1_to_te2", "flow_te2_to_te1"]

# Report path — fixed name, overwritten on every run
REPORT_PATH: str = "test_report_bgp_convergence.json"

# ---------------------------------------------------------------------------
# OTG Configuration (from bgp_convergence_cpdp.json, port locations injected)
# Port te1 -> location "veth-a"
# Port te2 -> location "veth-z"
# ---------------------------------------------------------------------------
OTG_CONFIG_JSON: str = r"""
{
  "ports": [
    { "name": "te1", "location": "veth-a" },
    { "name": "te2", "location": "veth-z" }
  ],
  "devices": [
    {
      "name": "device_te1",
      "ethernets": [
        {
          "name": "eth_te1",
          "connection": { "choice": "port_name", "port_name": "te1" },
          "mac": "00:11:01:00:00:01",
          "ipv4_addresses": [
            {
              "name": "ipv4_te1",
              "address": "192.168.1.1",
              "prefix": 24,
              "gateway": "192.168.1.2"
            }
          ]
        }
      ],
      "bgp": {
        "router_id": "1.1.1.1",
        "ipv4_interfaces": [
          {
            "ipv4_name": "ipv4_te1",
            "peers": [
              {
                "name": "bgp_peer_te1",
                "peer_address": "192.168.1.2",
                "as_type": "ebgp",
                "as_number": 65001,
                "v4_routes": [
                  {
                    "name": "routes_te1",
                    "addresses": [
                      { "address": "10.1.0.0", "prefix": 24, "count": 1, "step": 1 }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    },
    {
      "name": "device_te2",
      "ethernets": [
        {
          "name": "eth_te2",
          "connection": { "choice": "port_name", "port_name": "te2" },
          "mac": "00:11:02:00:00:01",
          "ipv4_addresses": [
            {
              "name": "ipv4_te2",
              "address": "192.168.1.2",
              "prefix": 24,
              "gateway": "192.168.1.1"
            }
          ]
        }
      ],
      "bgp": {
        "router_id": "2.2.2.2",
        "ipv4_interfaces": [
          {
            "ipv4_name": "ipv4_te2",
            "peers": [
              {
                "name": "bgp_peer_te2",
                "peer_address": "192.168.1.1",
                "as_type": "ebgp",
                "as_number": 65002,
                "advanced": { "passive_mode": true },
                "v4_routes": [
                  {
                    "name": "routes_te2",
                    "addresses": [
                      { "address": "10.2.0.0", "prefix": 24, "count": 1, "step": 1 }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    }
  ],
  "flows": [
    {
      "name": "flow_te1_to_te2",
      "tx_rx": {
        "choice": "port",
        "port": { "tx_name": "te1", "rx_names": ["te2"] }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "dst": { "choice": "value", "value": "00:11:02:00:00:01" },
            "src": { "choice": "value", "value": "00:11:01:00:00:01" }
          }
        },
        {
          "choice": "ipv4",
          "ipv4": {
            "src": { "choice": "value", "value": "10.1.0.1" },
            "dst": { "choice": "value", "value": "10.2.0.1" }
          }
        }
      ],
      "size":     { "choice": "fixed", "fixed": 512 },
      "rate":     { "choice": "pps",   "pps": 1000  },
      "duration": { "choice": "continuous" },
      "metrics":  { "enable": true }
    },
    {
      "name": "flow_te2_to_te1",
      "tx_rx": {
        "choice": "port",
        "port": { "tx_name": "te2", "rx_names": ["te1"] }
      },
      "packet": [
        {
          "choice": "ethernet",
          "ethernet": {
            "dst": { "choice": "value", "value": "00:11:01:00:00:01" },
            "src": { "choice": "value", "value": "00:11:02:00:00:01" }
          }
        },
        {
          "choice": "ipv4",
          "ipv4": {
            "src": { "choice": "value", "value": "10.2.0.1" },
            "dst": { "choice": "value", "value": "10.1.0.1" }
          }
        }
      ],
      "size":     { "choice": "fixed", "fixed": 512 },
      "rate":     { "choice": "pps",   "pps": 1000  },
      "duration": { "choice": "continuous" },
      "metrics":  { "enable": true }
    }
  ]
}
"""

# ===========================================================================
# CONNECTION
# ===========================================================================


def _connect(url: str, max_retries: int = 3) -> snappi.Api:
    """Connect to the OTG controller with exponential-backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            log.info("Connecting to %s (attempt %d/%d) ...", url, attempt, max_retries)
            api = snappi.api(location=url, verify=VERIFY_TLS)
            # Verify the controller responds before returning
            api.get_config()
            log.info("Connected successfully.")
            return api
        except Exception as exc:
            if attempt < max_retries:
                wait = 2 ** (attempt - 1)   # 1 s, 2 s, 4 s
                log.warning("Connection failed (%s). Retrying in %d s ...", exc, wait)
                time.sleep(wait)
            else:
                log.error("Could not connect after %d attempts.", max_retries)
                raise


# ===========================================================================
# CONFIG
# ===========================================================================


def _push_config(api: snappi.Api) -> snappi.Config:
    """Deserialise the embedded OTG JSON and push it to the controller."""
    log.info("Pushing OTG configuration ...")
    cfg = snappi.Config()
    cfg.deserialize(OTG_CONFIG_JSON)
    api.set_config(cfg)
    log.info(
        "Config applied: %d port(s), %d device(s), %d flow(s).",
        len(cfg.ports),
        len(cfg.devices),
        len(cfg.flows),
    )
    return cfg


# ===========================================================================
# PROTOCOL CONTROL
# ===========================================================================


def _start_protocols(api: snappi.Api) -> None:
    """Send the protocol-start control state."""
    log.info("Starting protocols ...")
    cs = snappi.ControlState()
    cs.protocol.choice = cs.protocol.ALL
    cs.protocol.all.state = cs.protocol.all.START
    api.set_control_state(cs)


def _stop_protocols(api: snappi.Api) -> None:
    """Send the protocol-stop control state (non-fatal on error)."""
    log.info("Stopping protocols ...")
    try:
        cs = snappi.ControlState()
        cs.protocol.choice = cs.protocol.ALL
        cs.protocol.all.state = cs.protocol.all.STOP
        api.set_control_state(cs)
    except Exception as exc:
        log.warning("Error stopping protocols (non-fatal): %s", exc)


# ===========================================================================
# BGP CONVERGENCE POLL
# ===========================================================================


def _get_bgp_session_count(api: snappi.Api) -> int:
    """
    Return the number of BGP sessions in the Established state.

    Tries the dedicated BGPv4 metrics endpoint first (req.BGPV4); falls back
    to device-level metrics if the controller does not expose that endpoint.
    This dual-path approach handles both ixia-c and KENG deployments.
    """
    # Primary: BGPv4-specific metrics (supported by ixia-c / KENG)
    try:
        req = snappi.MetricsRequest()
        req.choice = req.BGPV4
        res = api.get_metrics(req)
        return sum(1 for m in res.bgpv4_metrics if m.session_state in ("established", "up"))
    except Exception:
        pass

    # Fallback: device-level metrics
    try:
        req2 = snappi.MetricsRequest()
        req2.choice = req2.DEVICE
        res2 = api.get_metrics(req2)
        count = 0
        for dm in res2.device_metrics:
            if hasattr(dm, "bgp_session"):
                count += sum(1 for s in dm.bgp_session if s.session_state == "up")
        return count
    except Exception:
        return 0


def _wait_for_bgp(
    api: snappi.Api,
    expected: int,
    timeout_s: int,
    poll_s: int,
) -> bool:
    """
    Poll BGP session state until *expected* sessions reach Established,
    or until *timeout_s* seconds elapse.
    Returns True on success, False on timeout.
    """
    log.info(
        "Waiting for %d BGP session(s) to reach Established (timeout %d s) ...",
        expected,
        timeout_s,
    )
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        up = _get_bgp_session_count(api)
        elapsed = int(timeout_s - (deadline - time.monotonic()))
        log.info("  BGP sessions up: %d/%d  (%d s elapsed)", up, expected, elapsed)
        if up >= expected:
            log.info("BGP convergence achieved in ~%d s.", elapsed)
            return True
        time.sleep(poll_s)

    # Final check at deadline
    up = _get_bgp_session_count(api)
    log.error(
        "BGP convergence timeout (%d s): only %d/%d sessions Established.",
        timeout_s,
        up,
        expected,
    )
    return False


# ===========================================================================
# TRAFFIC CONTROL
# ===========================================================================


def _start_traffic(api: snappi.Api) -> None:
    """Start all flows."""
    log.info("Starting traffic ...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("Traffic started.")


def _stop_traffic(api: snappi.Api) -> None:
    """Stop all flows (non-fatal on error so cleanup always completes)."""
    log.info("Stopping traffic ...")
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


def _poll_metrics(
    api: snappi.Api,
    duration_s: int,
    interval_s: int,
) -> list[dict[str, Any]]:
    """
    Collect flow and port metrics every *interval_s* seconds for *duration_s*
    seconds.  Streams a live table row to stdout for every snapshot.
    Returns the full list of snapshots for the JSON report.
    """
    snapshots: list[dict[str, Any]] = []
    end_time = time.monotonic() + duration_s
    snapshot_num = 0

    col_w = 14
    header = (
        f"{'Elapsed':>8s}  "
        f"{'Flow':<26s}  "
        f"{'Tx Frames':>{col_w}s}  "
        f"{'Rx Frames':>{col_w}s}  "
        f"{'Loss %':>8s}  "
        f"{'Rx pps':>{col_w}s}"
    )
    separator = "-" * len(header)
    log.info("\n%s\n%s", header, separator)

    while time.monotonic() < end_time:
        # Sleep up to interval_s but never past end_time
        sleep_for = min(interval_s, max(0.0, end_time - time.monotonic()))
        time.sleep(sleep_for)

        snapshot_num += 1
        elapsed = int(duration_s - max(0.0, end_time - time.monotonic()))

        # Flow metrics — controller may drop connection at end of fixed_seconds duration
        try:
            freq = snappi.MetricsRequest()
            freq.choice = freq.FLOW
            fres = api.get_metrics(freq)

            # Port metrics
            preq = snappi.MetricsRequest()
            preq.choice = preq.PORT
            pres = api.get_metrics(preq)
        except Exception as exc:
            log.warning("Metrics fetch interrupted (likely end of fixed-duration flow): %s", exc)
            break

        flow_data: dict[str, Any] = {}
        for fm in fres.flow_metrics:
            tx = int(fm.frames_tx)
            rx = int(fm.frames_rx)
            loss_pct = ((tx - rx) / tx * 100.0) if tx > 0 else 0.0
            rx_pps = rx / interval_s if interval_s > 0 else 0.0
            flow_data[fm.name] = {
                "frames_tx": tx,
                "frames_rx": rx,
                "loss_pct": round(loss_pct, 6),
                "rx_pps": round(rx_pps, 1),
            }
            log.info(
                "%8d  %-26s  %14d  %14d  %8.4f  %14.1f",
                elapsed,
                fm.name,
                tx,
                rx,
                loss_pct,
                rx_pps,
            )

        port_data: dict[str, Any] = {}
        for pm in pres.port_metrics:
            port_data[pm.name] = {
                "frames_tx": int(pm.frames_tx),
                "frames_rx": int(pm.frames_rx),
                "bytes_tx": int(pm.bytes_tx),
                "bytes_rx": int(pm.bytes_rx),
                "link_state": getattr(pm, "link", "unknown"),
            }

        snapshots.append(
            {
                "snapshot": snapshot_num,
                "elapsed_s": elapsed,
                "flows": flow_data,
                "ports": port_data,
            }
        )

    log.info(separator)
    return snapshots


# ===========================================================================
# ASSERTIONS
# ===========================================================================


def _assert_bgp_sessions(api: snappi.Api, expected: int) -> dict[str, Any]:
    """Assert that at least *expected* BGP sessions are in Established state."""
    actual = _get_bgp_session_count(api)
    passed = actual >= expected
    result: dict[str, Any] = {
        "name": "bgp_sessions_established",
        "type": "bgp_state",
        "expected_min": expected,
        "actual": actual,
        "passed": passed,
    }
    status = "PASS" if passed else "FAIL"
    log.info(
        "[Assertion] bgp_sessions_established : %s  (expected >=%d, actual %d)",
        status,
        expected,
        actual,
    )
    return result


def _assert_flow_loss(
    api: snappi.Api,
    flow_names: list[str],
    max_loss_pct: float,
) -> list[dict[str, Any]]:
    """
    Assert that packet loss on each named flow is below *max_loss_pct* percent.
    Uses the final cumulative Tx/Rx counters after traffic has been stopped.
    """
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    metrics_by_name = {fm.name: fm for fm in res.flow_metrics}
    results: list[dict[str, Any]] = []

    for name in flow_names:
        if name not in metrics_by_name:
            results.append(
                {
                    "name": f"loss_lt_{max_loss_pct}pct_{name}",
                    "type": "flow_loss",
                    "flow": name,
                    "max_loss_pct": max_loss_pct,
                    "passed": False,
                    "error": "Flow not found in metrics response",
                }
            )
            log.error(
                "[Assertion] loss_lt_%.1fpct_%s : FAIL  (flow not found in metrics)",
                max_loss_pct,
                name,
            )
            continue

        fm = metrics_by_name[name]
        tx = int(fm.frames_tx)
        rx = int(fm.frames_rx)
        lost = tx - rx
        loss_pct = (lost / tx * 100.0) if tx > 0 else 0.0
        passed = loss_pct < max_loss_pct

        result: dict[str, Any] = {
            "name": f"loss_lt_{max_loss_pct}pct_{name}",
            "type": "flow_loss",
            "flow": name,
            "frames_tx": tx,
            "frames_rx": rx,
            "frames_lost": lost,
            "loss_pct": round(loss_pct, 6),
            "max_loss_pct": max_loss_pct,
            "passed": passed,
        }
        status = "PASS" if passed else "FAIL"
        log.info(
            "[Assertion] loss_lt_%.1fpct_%s : %s  "
            "(tx=%d, rx=%d, lost=%d, loss=%.6f%%)",
            max_loss_pct,
            name,
            status,
            tx,
            rx,
            lost,
            loss_pct,
        )
        results.append(result)

    return results


# ===========================================================================
# REPORT
# ===========================================================================


def _save_report(data: dict[str, Any], path: str) -> None:
    """Serialise test results to *path* (overwrites on every run)."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    log.info("Report written to %s", path)


# ===========================================================================
# MAIN TEST EXECUTION
# ===========================================================================


def run_test() -> bool:
    """
    Execute the BGP convergence test end-to-end.
    Returns True if all assertions pass, False otherwise.
    The JSON report is always written, even on failure.
    """
    log.info("=" * 72)
    log.info("Test       : %s", TEST_NAME)
    log.info("Controller : %s", CONTROLLER_URL)
    log.info("Duration   : %d s  |  Metrics interval : %d s", TEST_DURATION_S, METRICS_INTERVAL_S)
    log.info("BGP timeout: %d s  |  Loss threshold   : %.1f%%", BGP_CONVERGENCE_TIMEOUT_S, MAX_LOSS_PCT)
    log.info("=" * 72)

    started_at = datetime.now(tz=timezone.utc).isoformat()
    api: snappi.Api | None = None
    traffic_started: bool = False
    protocols_started: bool = False
    all_assertions: list[dict[str, Any]] = []
    metric_snapshots: list[dict[str, Any]] = []
    overall_passed: bool = False

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
        # Step 3: Start protocols and poll for BGP convergence
        # ------------------------------------------------------------------
        _start_protocols(api)
        protocols_started = True

        bgp_converged = _wait_for_bgp(
            api,
            expected=EXPECTED_BGP_SESSIONS,
            timeout_s=BGP_CONVERGENCE_TIMEOUT_S,
            poll_s=BGP_CONVERGENCE_POLL_S,
        )

        if not bgp_converged:
            # Record BGP assertion as failed; skip traffic phase entirely
            log.error(
                "BGP did not converge within %d s. "
                "Recording assertion failure and skipping traffic phase.",
                BGP_CONVERGENCE_TIMEOUT_S,
            )
            all_assertions.append(
                {
                    "name": "bgp_sessions_established",
                    "type": "bgp_state",
                    "expected_min": EXPECTED_BGP_SESSIONS,
                    "actual": _get_bgp_session_count(api),
                    "passed": False,
                    "error": "BGP convergence timeout",
                }
            )
            # Loss assertions will show 0/0 — record them so the report is complete
            all_assertions.extend(
                _assert_flow_loss(api, FLOWS_UNDER_TEST, MAX_LOSS_PCT)
            )
        else:
            # --------------------------------------------------------------
            # Step 4: Start traffic
            # --------------------------------------------------------------
            _start_traffic(api)
            traffic_started = True

            # --------------------------------------------------------------
            # Step 5: Collect live metrics for 120 s (prints every 5 s)
            # --------------------------------------------------------------
            log.info(
                "Collecting metrics for %d s (interval %d s) ...",
                TEST_DURATION_S,
                METRICS_INTERVAL_S,
            )
            metric_snapshots = _poll_metrics(
                api,
                duration_s=TEST_DURATION_S,
                interval_s=METRICS_INTERVAL_S,
            )

            # --------------------------------------------------------------
            # Step 6: Stop traffic before final assertions
            # --------------------------------------------------------------
            _stop_traffic(api)
            traffic_started = False

            # --------------------------------------------------------------
            # Step 7: Validate assertions against final counters
            # --------------------------------------------------------------
            log.info("-" * 72)
            log.info("Validating assertions ...")
            all_assertions.append(
                _assert_bgp_sessions(api, EXPECTED_BGP_SESSIONS)
            )
            all_assertions.extend(
                _assert_flow_loss(api, FLOWS_UNDER_TEST, MAX_LOSS_PCT)
            )

        # ------------------------------------------------------------------
        # Step 8: Compute overall result and print summary
        # ------------------------------------------------------------------
        overall_passed = all(a["passed"] for a in all_assertions)
        verdict = "PASSED" if overall_passed else "FAILED"

        log.info("=" * 72)
        log.info("SUMMARY")
        log.info("-" * 72)
        for a in all_assertions:
            status = "PASS" if a["passed"] else "FAIL"
            log.info("  [%s]  %s", status, a["name"])
        log.info("-" * 72)
        log.info("Overall result : %s", verdict)
        log.info("Report         : %s", REPORT_PATH)
        log.info("=" * 72)

    except KeyboardInterrupt:
        log.warning("Test interrupted by user (Ctrl+C).")
        overall_passed = False

    except Exception as exc:
        log.error("Unhandled error: %s", exc, exc_info=True)
        overall_passed = False

    finally:
        # ------------------------------------------------------------------
        # Cleanup — always runs, even on error or keyboard interrupt
        # ------------------------------------------------------------------
        if api is not None:
            if traffic_started:
                _stop_traffic(api)
            if protocols_started:
                _stop_protocols(api)

    # ------------------------------------------------------------------------
    # Step 9: Write JSON report (always, regardless of pass/fail)
    # ------------------------------------------------------------------------
    finished_at = datetime.now(tz=timezone.utc).isoformat()
    report: dict[str, Any] = {
        "test_name": TEST_NAME,
        "controller": CONTROLLER_URL,
        "started_at": started_at,
        "finished_at": finished_at,
        "test_duration_s": TEST_DURATION_S,
        "metrics_interval_s": METRICS_INTERVAL_S,
        "bgp_convergence_timeout_s": BGP_CONVERGENCE_TIMEOUT_S,
        "loss_threshold_pct": MAX_LOSS_PCT,
        "overall_passed": overall_passed,
        "assertions": all_assertions,
        "metric_snapshots": metric_snapshots,
    }
    _save_report(report, REPORT_PATH)

    return overall_passed


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
