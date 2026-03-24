#!/usr/bin/env python3
"""
BGP Back-to-Back Convergence Test
==================================
Generated : 2026-03-22
OTG Config : otg_config.json (embedded)
Controller : https://localhost:8443

Topology
--------
  P1 (veth-a)                    P2 (veth-z)
  device1                        device2
  AS 65001  <-- eBGP session --> AS 65002
  192.168.1.1                    192.168.1.2
  Advertises: 10.1.0.0/24        Advertises: 10.2.0.0/24

Test Flow
---------
  1. Push OTG config to controller
  2. Start protocols; poll until both eBGP sessions reach Established (timeout 60 s)
  3. Start bidirectional traffic: flow_P1_to_P2 and flow_P2_to_P1 at 1234 pps each
  4. Collect port and flow metrics every 5 s for 120 s
  5. Stop traffic; stop protocols
  6. Assert: both BGP sessions established, zero packet loss on both flows
  7. Write JSON report to test_report_<timestamp>.json

Usage
-----
  pip install snappi
  python test_bgp_b2b.py

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
log = logging.getLogger("bgp_b2b")

# ===========================================================================
# EMBEDDED CONFIGURATION — all infrastructure details live here
# ===========================================================================

# Controller connection
CONTROLLER_URL: str = "https://localhost:8443"
VERIFY_TLS: bool = False          # set True + supply CA path for production

# Test parameters (from infrastructure.yaml)
TEST_NAME: str = "bgp_b2b_convergence"
METRICS_INTERVAL_S: int = 5
TEST_DURATION_S: int = 120
BGP_CONVERGENCE_TIMEOUT_S: int = 60
BGP_CONVERGENCE_POLL_S: int = 2
STOP_ON_FAILURE: bool = False

# Assertions
#   bgp_sessions    — both BGP peers must reach Established state
#   zero_flow_loss  — zero frames lost on each flow
EXPECTED_BGP_SESSIONS: int = 2
FLOWS_UNDER_TEST: list[str] = ["flow_P1_to_P2", "flow_P2_to_P1"]

# OTG Configuration (verbatim from otg_config.json)
OTG_CONFIG_JSON: str = r"""
{
  "ports": [
    { "name": "P1", "location": "veth-a" },
    { "name": "P2", "location": "veth-z" }
  ],
  "devices": [
    {
      "name": "device1",
      "ethernets": [
        {
          "name": "device1.eth1",
          "connection": { "choice": "port_name", "port_name": "P1" },
          "mac": "00:11:01:00:00:01",
          "ipv4_addresses": [
            { "name": "device1.ipv4", "address": "192.168.1.1", "prefix": 24, "gateway": "192.168.1.2" }
          ]
        }
      ],
      "bgp": {
        "router_id": "192.0.2.1",
        "ipv4_interfaces": [
          {
            "ipv4_name": "device1.ipv4",
            "peers": [
              {
                "name": "device1.bgp.peer1",
                "peer_address": "192.168.1.2",
                "as_type": "ebgp",
                "as_number": 65002,
                "v4_routes": [
                  {
                    "name": "device1.bgp.peer1.routes",
                    "next_hop_mode": "manual",
                    "next_hop_address_type": "ipv4",
                    "next_hop_ipv4_address": "192.168.1.1",
                    "addresses": [{ "address": "10.1.0.0", "prefix": 24, "count": 1 }]
                  }
                ]
              }
            ]
          }
        ]
      }
    },
    {
      "name": "device2",
      "ethernets": [
        {
          "name": "device2.eth1",
          "connection": { "choice": "port_name", "port_name": "P2" },
          "mac": "00:11:02:00:00:01",
          "ipv4_addresses": [
            { "name": "device2.ipv4", "address": "192.168.1.2", "prefix": 24, "gateway": "192.168.1.1" }
          ]
        }
      ],
      "bgp": {
        "router_id": "192.0.2.2",
        "ipv4_interfaces": [
          {
            "ipv4_name": "device2.ipv4",
            "peers": [
              {
                "name": "device2.bgp.peer1",
                "peer_address": "192.168.1.1",
                "as_type": "ebgp",
                "as_number": 65001,
                "v4_routes": [
                  {
                    "name": "device2.bgp.peer1.routes",
                    "next_hop_mode": "manual",
                    "next_hop_address_type": "ipv4",
                    "next_hop_ipv4_address": "192.168.1.2",
                    "addresses": [{ "address": "10.2.0.0", "prefix": 24, "count": 1 }]
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
      "name": "flow_P1_to_P2",
      "tx_rx": { "choice": "port", "port": { "tx_name": "P1", "rx_names": ["P2"] } },
      "packet": [
        { "choice": "ethernet", "ethernet": { "dst": {"choice": "value", "value": "00:11:02:00:00:01"}, "src": {"choice": "value", "value": "00:11:01:00:00:01"} } },
        { "choice": "ipv4", "ipv4": { "src": {"choice": "value", "value": "10.1.0.1"}, "dst": {"choice": "value", "value": "10.2.0.1"} } }
      ],
      "rate": {"choice": "pps", "pps": 1234},
      "duration": {"choice": "fixed_seconds", "fixed_seconds": {"seconds": 120}},
      "metrics": {"enable": true}
    },
    {
      "name": "flow_P2_to_P1",
      "tx_rx": { "choice": "port", "port": { "tx_name": "P2", "rx_names": ["P1"] } },
      "packet": [
        { "choice": "ethernet", "ethernet": { "dst": {"choice": "value", "value": "00:11:01:00:00:01"}, "src": {"choice": "value", "value": "00:11:02:00:00:01"} } },
        { "choice": "ipv4", "ipv4": { "src": {"choice": "value", "value": "10.2.0.1"}, "dst": {"choice": "value", "value": "10.1.0.1"} } }
      ],
      "rate": {"choice": "pps", "pps": 1234},
      "duration": {"choice": "fixed_seconds", "fixed_seconds": {"seconds": 120}},
      "metrics": {"enable": true}
    }
  ]
}
"""

# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================


def _connect(url: str, max_retries: int = 3) -> snappi.Api:
    """Connect to the OTG controller with exponential-backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            log.info("Connecting to %s (attempt %d/%d)...", url, attempt, max_retries)
            api = snappi.api(location=url, verify=VERIFY_TLS)
            # Ping the controller by fetching its config
            api.get_config()
            log.info("Connected successfully.")
            return api
        except Exception as exc:
            if attempt < max_retries:
                wait = 2 ** (attempt - 1)  # 1 s, 2 s, 4 s
                log.warning("Connection failed (%s). Retrying in %d s...", exc, wait)
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
        "Config loaded: %d port(s), %d device(s), %d flow(s).",
        len(cfg.ports),
        len(cfg.devices),
        len(cfg.flows),
    )
    return cfg


def _get_bgp_session_count(api: snappi.Api) -> int:
    """Return the current number of BGP sessions in the Established state."""
    req = snappi.MetricsRequest()
    req.choice = req.BGPV4
    try:
        res = api.get_metrics(req)
        return sum(
            1 for m in res.bgpv4_metrics if m.session_state == "established"
        )
    except Exception:
        # Fallback: query via device metrics if bgpv4 path not supported
        try:
            req2 = snappi.MetricsRequest()
            req2.choice = req2.DEVICE
            res2 = api.get_metrics(req2)
            count = 0
            for device_metric in res2.device_metrics:
                if hasattr(device_metric, "bgp_session"):
                    count += sum(
                        1
                        for s in device_metric.bgp_session
                        if s.session_state == "up"
                    )
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
    Poll BGP session state until all expected sessions reach Established.
    Returns True on success, False on timeout.
    """
    log.info(
        "Waiting for %d BGP session(s) to reach Established (timeout %d s)...",
        expected,
        timeout_s,
    )
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        up = _get_bgp_session_count(api)
        elapsed = timeout_s - int(deadline - time.monotonic())
        log.info("  BGP sessions up: %d/%d  (%d s elapsed)", up, expected, elapsed)
        if up >= expected:
            log.info("BGP convergence achieved in ~%d s.", elapsed)
            return True
        time.sleep(poll_s)

    up = _get_bgp_session_count(api)
    log.error(
        "BGP convergence timeout (%d s): %d/%d sessions established.",
        timeout_s,
        up,
        expected,
    )
    return False


def _start_protocols(api: snappi.Api) -> None:
    """Send the protocol-start control state to the controller."""
    log.info("Starting protocols...")
    cs = snappi.ControlState()
    cs.protocol.state = snappi.ControlState.Protocol.start
    api.set_control_state(cs)


def _stop_protocols(api: snappi.Api) -> None:
    """Send the protocol-stop control state to the controller."""
    log.info("Stopping protocols...")
    try:
        cs = snappi.ControlState()
        cs.protocol.state = snappi.ControlState.Protocol.stop
        api.set_control_state(cs)
    except Exception as exc:
        log.warning("Error stopping protocols (non-fatal): %s", exc)


def _start_traffic(api: snappi.Api) -> None:
    """Start all flows."""
    log.info("Starting traffic...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("Traffic started.")


def _stop_traffic(api: snappi.Api) -> None:
    """Stop all flows (non-fatal on error so cleanup always completes)."""
    log.info("Stopping traffic...")
    try:
        cs = snappi.ControlState()
        cs.traffic.flow_transmit.state = "stop"
        api.set_control_state(cs)
        log.info("Traffic stopped.")
    except Exception as exc:
        log.warning("Error stopping traffic (non-fatal): %s", exc)


def _poll_metrics(
    api: snappi.Api,
    duration_s: int,
    interval_s: int,
) -> list[dict[str, Any]]:
    """
    Collect flow and port metrics every *interval_s* seconds for *duration_s*
    seconds.  Returns a list of metric snapshots.
    """
    snapshots: list[dict[str, Any]] = []
    end_time = time.monotonic() + duration_s
    snapshot_num = 0

    col_w = 14
    header = (
        f"{'Elapsed':>8s}  "
        f"{'Flow':<24s}  "
        f"{'Tx Frames':>{col_w}s}  "
        f"{'Rx Frames':>{col_w}s}  "
        f"{'Loss %':>8s}  "
        f"{'Rx pps':>{col_w}s}"
    )
    separator = "-" * len(header)
    log.info("\n%s\n%s", header, separator)

    while time.monotonic() < end_time:
        time.sleep(min(interval_s, max(0, end_time - time.monotonic())))
        snapshot_num += 1
        elapsed = int(duration_s - (end_time - time.monotonic()))

        # --- flow metrics ---
        freq = snappi.MetricsRequest()
        freq.choice = freq.FLOW
        fres = api.get_metrics(freq)

        # --- port metrics ---
        preq = snappi.MetricsRequest()
        preq.choice = preq.PORT
        pres = api.get_metrics(preq)

        flow_data: dict[str, Any] = {}
        for fm in fres.flow_metrics:
            tx = int(fm.frames_tx)
            rx = int(fm.frames_rx)
            loss_pct = ((tx - rx) / tx * 100.0) if tx > 0 else 0.0
            rate_rx = rx / interval_s if interval_s > 0 else 0.0
            flow_data[fm.name] = {
                "frames_tx": tx,
                "frames_rx": rx,
                "loss_pct": round(loss_pct, 6),
                "rx_pps": round(rate_rx, 1),
            }
            log.info(
                "%8d  %-24s  %14d  %14d  %8.4f  %14.1f",
                elapsed,
                fm.name,
                tx,
                rx,
                loss_pct,
                rate_rx,
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
# ASSERTION VALIDATORS
# ===========================================================================


def _assert_bgp_sessions(api: snappi.Api, expected: int) -> dict[str, Any]:
    """Assert that the expected number of BGP sessions are Established."""
    actual = _get_bgp_session_count(api)
    passed = actual >= expected
    result: dict[str, Any] = {
        "name": "bgp_sessions_established",
        "type": "bgp_state",
        "expected": expected,
        "actual": actual,
        "passed": passed,
    }
    status = "PASS" if passed else "FAIL"
    log.info(
        "[Assertion] bgp_sessions_established: %s  (expected >=%d, actual %d)",
        status,
        expected,
        actual,
    )
    return result


def _assert_zero_flow_loss(
    api: snappi.Api,
    flow_names: list[str],
) -> list[dict[str, Any]]:
    """Assert zero packet loss on each named flow (Tx == Rx)."""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    metrics_by_name = {fm.name: fm for fm in res.flow_metrics}
    results: list[dict[str, Any]] = []

    for name in flow_names:
        if name not in metrics_by_name:
            results.append(
                {
                    "name": f"zero_loss_{name}",
                    "type": "flow_loss",
                    "flow": name,
                    "passed": False,
                    "error": "Flow not found in metrics response",
                }
            )
            log.error("[Assertion] zero_loss_%s: FAIL  (flow not found)", name)
            continue

        fm = metrics_by_name[name]
        tx = int(fm.frames_tx)
        rx = int(fm.frames_rx)
        loss = tx - rx
        passed = loss == 0
        loss_pct = (loss / tx * 100.0) if tx > 0 else 0.0
        result: dict[str, Any] = {
            "name": f"zero_loss_{name}",
            "type": "flow_loss",
            "flow": name,
            "frames_tx": tx,
            "frames_rx": rx,
            "frames_lost": loss,
            "loss_pct": round(loss_pct, 6),
            "passed": passed,
        }
        status = "PASS" if passed else "FAIL"
        log.info(
            "[Assertion] zero_loss_%s: %s  (tx=%d, rx=%d, lost=%d, loss=%.6f%%)",
            name,
            status,
            tx,
            rx,
            loss,
            loss_pct,
        )
        results.append(result)

    return results


# ===========================================================================
# REPORT
# ===========================================================================


def _save_report(data: dict[str, Any]) -> str:
    """Serialise test results to a timestamped JSON file."""
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
    """
    Execute the BGP back-to-back convergence test.
    Returns True if all assertions pass, False otherwise.
    """
    log.info("=" * 70)
    log.info("Test : %s", TEST_NAME)
    log.info("Controller : %s", CONTROLLER_URL)
    log.info("Duration   : %d s  |  Metrics interval: %d s", TEST_DURATION_S, METRICS_INTERVAL_S)
    log.info("=" * 70)

    started_at = datetime.now(tz=timezone.utc).isoformat()
    api: snappi.Api | None = None
    traffic_started = False
    protocols_started = False
    all_assertions: list[dict[str, Any]] = []
    metric_snapshots: list[dict[str, Any]] = []
    overall_passed = False

    try:
        # ------------------------------------------------------------------
        # Step 1: Connect
        # ------------------------------------------------------------------
        api = _connect(CONTROLLER_URL)

        # ------------------------------------------------------------------
        # Step 2: Push config
        # ------------------------------------------------------------------
        _push_config(api)

        # ------------------------------------------------------------------
        # Step 3: Start protocols and wait for BGP convergence
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
            log.error(
                "BGP did not converge within %d s. "
                "Proceeding to collect final assertion state before cleanup.",
                BGP_CONVERGENCE_TIMEOUT_S,
            )
            # Record the BGP assertion as failed and skip traffic
            all_assertions.append(
                {
                    "name": "bgp_sessions_established",
                    "type": "bgp_state",
                    "expected": EXPECTED_BGP_SESSIONS,
                    "actual": _get_bgp_session_count(api),
                    "passed": False,
                    "error": "BGP convergence timeout",
                }
            )
            # Still attempt zero-loss assertion (will report 0 tx/rx)
            all_assertions.extend(_assert_zero_flow_loss(api, FLOWS_UNDER_TEST))
        else:
            # --------------------------------------------------------------
            # Step 4: Start traffic
            # --------------------------------------------------------------
            _start_traffic(api)
            traffic_started = True

            # --------------------------------------------------------------
            # Step 5: Collect metrics
            # --------------------------------------------------------------
            log.info(
                "Collecting metrics for %d s (interval %d s)...",
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
            # Step 7: Validate assertions
            # --------------------------------------------------------------
            log.info("-" * 70)
            log.info("Validating assertions...")
            all_assertions.append(_assert_bgp_sessions(api, EXPECTED_BGP_SESSIONS))
            all_assertions.extend(_assert_zero_flow_loss(api, FLOWS_UNDER_TEST))

        overall_passed = all(a["passed"] for a in all_assertions)
        verdict = "PASSED" if overall_passed else "FAILED"
        log.info("=" * 70)
        log.info("Test result: %s", verdict)
        log.info("=" * 70)

    except KeyboardInterrupt:
        log.warning("Test interrupted by user (Ctrl+C).")
        overall_passed = False

    except Exception as exc:
        log.error("Unhandled error: %s", exc, exc_info=True)
        overall_passed = False

    finally:
        # ------------------------------------------------------------------
        # Cleanup — always runs
        # ------------------------------------------------------------------
        if api is not None:
            if traffic_started:
                _stop_traffic(api)
            if protocols_started:
                _stop_protocols(api)

    # ------------------------------------------------------------------------
    # Write report
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
        "overall_passed": overall_passed,
        "assertions": all_assertions,
        "metric_snapshots": metric_snapshots,
    }
    _save_report(report)

    return overall_passed


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
