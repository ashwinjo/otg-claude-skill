#!/usr/bin/env python3
"""
2xIxia + FRR DUT BGP Routing Test
===================================
Generated  : 2026-03-22
OTG Config : 2ixia_frr_bgp.json (embedded)
Controllers: IXIA_A https://172.20.20.4:8443
             IXIA_Z https://172.20.20.3:8443

Topology
--------
  P1 (eth1 @ 172.20.20.4:8443)             P2 (eth1 @ 172.20.20.3:8443)
  IXIA_A                                   IXIA_Z
  AS 65001  ──── eBGP to FRR DUT ────  AS 65002
  10.0.1.1/24                              10.0.2.1/24
  gateway: 10.0.1.254 (FRR eth1)          gateway: 10.0.2.254 (FRR eth2)

  FRR DUT: 10.0.1.254 (eth1) <-> 10.0.2.254 (eth2)

  Flow : A_to_Z  (P1 → P2, unidirectional, 500 pps, 64-byte frames, continuous)

Test Flow
---------
  1. Connect to both controllers (A at 172.20.20.4, Z at 172.20.20.3)
     — Snappi handles multi-controller natively via port location strings
  2. Deserialise embedded OTG config and push it to the controller
  3. Start all protocols (eBGP sessions to FRR DUT from both sides)
  4. Poll BGPv4 session state until both peers reach "up" (timeout 120 s)
  5. Start unidirectional traffic: A_to_Z at 500 pps
  6. Collect flow and port metrics every 5 s for 60 s
  7. Stop traffic programmatically (continuous duration — no fixed_seconds)
  8. Collect final BGP, flow, and port metrics
  9. Validate assertions:
       - IXIA_A_bgp_peer session_state == "up"
       - IXIA_Z_bgp_peer session_state == "up"
       - A_to_Z frames_tx > 0
       - A_to_Z frames_rx > 0
       - A_to_Z frames_tx == frames_rx  (zero loss)
 10. Write JSON report to test_report_<timestamp>.json
 11. Cleanup: stop traffic, stop protocols

Usage
-----
  pip install snappi
  python3 test_2ixia_frr_bgp.py

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
# Suppress TLS warnings for self-signed certificates (Containerlab lab env)
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
log = logging.getLogger("2ixia_frr_bgp")

# ===========================================================================
# EMBEDDED CONFIGURATION — all infrastructure details live here
# ===========================================================================

# Multi-controller setup: Snappi resolves each port to its controller via
# the "location" field format: "<controller_ip>:<port>+<interface>"
# No extra code is required — set_config() dispatches to both controllers.
CONTROLLER_A_URL: str = "https://172.20.20.4:8443"   # Primary (used for API handle)
CONTROLLER_Z_URL: str = "https://172.20.20.3:8443"   # Referenced in port location
VERIFY_TLS: bool = False          # Self-signed certs in Containerlab; set True for prod

# Test parameters
TEST_NAME: str = "2ixia_frr_bgp_routing"
METRICS_INTERVAL_S: int = 5
TEST_DURATION_S: int = 60
BGP_CONVERGENCE_TIMEOUT_S: int = 120
BGP_CONVERGENCE_POLL_S: int = 3

# Assertions
EXPECTED_BGP_PEER_NAMES: list[str] = ["IXIA_A_bgp_peer", "IXIA_Z_bgp_peer"]
FLOW_UNDER_TEST: str = "A_to_Z"

# OTG Configuration (verbatim from 2ixia_frr_bgp.json)
# Port locations use the multi-controller format: "<ip>:<port>+<interface>"
# Snappi splits each location and routes config to the correct controller.
OTG_CONFIG_JSON: str = r"""
{
  "ports": [
    {
      "name": "P1",
      "location": "172.20.20.4:8443+eth1"
    },
    {
      "name": "P2",
      "location": "172.20.20.3:8443+eth1"
    }
  ],
  "devices": [
    {
      "name": "IXIA_A",
      "ethernets": [
        {
          "name": "IXIA_A_eth1",
          "connection": {
            "choice": "port_name",
            "port_name": "P1"
          },
          "mac": "00:11:01:00:00:01",
          "ipv4_addresses": [
            {
              "name": "IXIA_A_ipv4",
              "address": "10.0.1.1",
              "prefix": 24,
              "gateway": "10.0.1.254"
            }
          ]
        }
      ],
      "bgp": {
        "router_id": "10.0.1.1",
        "ipv4_interfaces": [
          {
            "ipv4_name": "IXIA_A_ipv4",
            "peers": [
              {
                "name": "IXIA_A_bgp_peer",
                "peer_address": "10.0.1.254",
                "as_type": "ebgp",
                "as_number": 65001,
                "v4_routes": [
                  {
                    "name": "IXIA_A_routes",
                    "addresses": [
                      {
                        "address": "10.0.1.0",
                        "prefix": 24,
                        "count": 1,
                        "step": 1
                      }
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
      "name": "IXIA_Z",
      "ethernets": [
        {
          "name": "IXIA_Z_eth1",
          "connection": {
            "choice": "port_name",
            "port_name": "P2"
          },
          "mac": "00:11:02:00:00:01",
          "ipv4_addresses": [
            {
              "name": "IXIA_Z_ipv4",
              "address": "10.0.2.1",
              "prefix": 24,
              "gateway": "10.0.2.254"
            }
          ]
        }
      ],
      "bgp": {
        "router_id": "10.0.2.1",
        "ipv4_interfaces": [
          {
            "ipv4_name": "IXIA_Z_ipv4",
            "peers": [
              {
                "name": "IXIA_Z_bgp_peer",
                "peer_address": "10.0.2.254",
                "as_type": "ebgp",
                "as_number": 65002,
                "v4_routes": [
                  {
                    "name": "IXIA_Z_routes",
                    "addresses": [
                      {
                        "address": "10.0.2.0",
                        "prefix": 24,
                        "count": 1,
                        "step": 1
                      }
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
      "name": "A_to_Z",
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
            "dst": {
              "choice": "value",
              "value": "00:11:02:00:00:01"
            },
            "src": {
              "choice": "value",
              "value": "00:11:01:00:00:01"
            }
          }
        },
        {
          "choice": "ipv4",
          "ipv4": {
            "src": {
              "choice": "value",
              "value": "10.0.1.1"
            },
            "dst": {
              "choice": "value",
              "value": "10.0.2.1"
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
        "pps": 500
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
# HELPER FUNCTIONS
# ===========================================================================


def _connect(url: str, max_retries: int = 3) -> snappi.Api:
    """
    Connect to the primary OTG controller with exponential-backoff retry.

    In a multi-controller topology the Snappi API handle connects to one
    controller; set_config() dispatches each port's sub-config to the
    correct controller based on the port location string.
    """
    for attempt in range(1, max_retries + 1):
        try:
            log.info(
                "Connecting to %s (attempt %d/%d)...", url, attempt, max_retries
            )
            api = snappi.api(location=url, verify=VERIFY_TLS)
            # Validate reachability by fetching the current config
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
    """
    Deserialise the embedded OTG JSON and push it to the controller(s).

    Uses cfg.deserialize() — the correct Snappi SDK method.
    Do NOT use cfg.loads() (that is Python's json module, not Snappi).
    """
    log.info("Deserialising embedded OTG config...")
    cfg = snappi.Config()
    cfg.deserialize(OTG_CONFIG_JSON)
    log.info(
        "Pushing config: %d port(s), %d device(s), %d flow(s).",
        len(cfg.ports),
        len(cfg.devices),
        len(cfg.flows),
    )
    api.set_config(cfg)
    log.info("Config pushed successfully.")
    return cfg


def _get_bgpv4_states(api: snappi.Api) -> dict[str, str]:
    """
    Return a mapping of {peer_name: session_state} for all BGPv4 peers.

    ixia-c reports session_state as "up" (not "established").
    Both values are accepted here for forward compatibility.
    """
    req = snappi.MetricsRequest()
    req.choice = req.BGPV4
    try:
        res = api.get_metrics(req)
        return {m.name: m.session_state for m in res.bgpv4_metrics}
    except Exception as exc:
        log.debug("BGPv4 metrics unavailable: %s", exc)
        return {}


def _count_bgp_sessions_up(states: dict[str, str]) -> int:
    """Count how many BGPv4 sessions are in the 'up' or 'established' state."""
    return sum(
        1 for state in states.values() if state in ("up", "established")
    )


def _wait_for_bgp(
    api: snappi.Api,
    peer_names: list[str],
    timeout_s: int,
    poll_s: int,
) -> bool:
    """
    Poll BGPv4 session state until all named peers reach 'up'.
    Returns True on success, False on timeout.
    """
    expected = len(peer_names)
    log.info(
        "Waiting for %d BGP peer(s) to reach 'up' (timeout %d s, poll %d s)...",
        expected,
        timeout_s,
        poll_s,
    )
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        states = _get_bgpv4_states(api)
        up_count = _count_bgp_sessions_up(states)
        elapsed = int(timeout_s - (deadline - time.monotonic()))

        # Show per-peer state for visibility
        peer_status = ", ".join(
            f"{n}={states.get(n, 'unknown')}" for n in peer_names
        )
        log.info(
            "  BGP sessions up: %d/%d  [%s]  (%d s elapsed)",
            up_count,
            expected,
            peer_status,
            elapsed,
        )

        # Check each named peer individually
        all_up = all(
            states.get(name) in ("up", "established") for name in peer_names
        )
        if all_up:
            log.info("All BGP peers are up. Convergence achieved in ~%d s.", elapsed)
            return True

        time.sleep(poll_s)

    # Final state on timeout
    states = _get_bgpv4_states(api)
    up_count = _count_bgp_sessions_up(states)
    log.error(
        "BGP convergence timeout (%d s): %d/%d sessions up. States: %s",
        timeout_s,
        up_count,
        expected,
        states,
    )
    return False


def _start_protocols(api: snappi.Api) -> None:
    """
    Start all protocols on both controllers.

    Correct ControlState API pattern (fixes.md: CLI/API — ControlState.Protocol):
      cs.protocol.choice = cs.protocol.ALL
      cs.protocol.all.state = cs.protocol.all.START
    Never use: snappi.ControlState.Protocol.start  (AttributeError)
    """
    log.info("Starting all protocols...")
    cs = snappi.ControlState()
    cs.protocol.choice = cs.protocol.ALL
    cs.protocol.all.state = cs.protocol.all.START
    api.set_control_state(cs)
    log.info("Protocol start command sent.")


def _stop_protocols(api: snappi.Api) -> None:
    """Stop all protocols (non-fatal on error so cleanup always completes)."""
    log.info("Stopping all protocols...")
    try:
        cs = snappi.ControlState()
        cs.protocol.choice = cs.protocol.ALL
        cs.protocol.all.state = cs.protocol.all.STOP
        api.set_control_state(cs)
        log.info("Protocols stopped.")
    except Exception as exc:
        log.warning("Error stopping protocols (non-fatal): %s", exc)


def _start_traffic(api: snappi.Api) -> None:
    """Start all flows."""
    log.info("Starting traffic flow: %s...", FLOW_UNDER_TEST)
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("Traffic started.")


def _stop_traffic(api: snappi.Api) -> None:
    """
    Stop all flows programmatically.

    Flow duration is 'continuous' — we never use fixed_seconds because
    keng-controller v1.48.0-5 crashes when fixed_seconds flows self-terminate.
    Always stop traffic explicitly with set_control_state().
    """
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
    Collect flow and port metrics every interval_s seconds for duration_s seconds.
    Prints a live table to stdout and returns a list of snapshot dicts.

    No latency or loss metrics are requested — ixia-c-one (keng-controller
    v1.48.0-5) does not support flow-level latency or loss metric fields.
    Basic frame counters (frames_tx, frames_rx) are available on all ports.
    """
    snapshots: list[dict[str, Any]] = []
    end_time = time.monotonic() + duration_s
    snapshot_num = 0

    col_w = 14
    header = (
        f"{'Elapsed':>8s}  "
        f"{'Flow':<20s}  "
        f"{'Tx Frames':>{col_w}s}  "
        f"{'Rx Frames':>{col_w}s}  "
        f"{'Loss %':>8s}  "
        f"{'Rx pps':>{col_w}s}"
    )
    separator = "-" * len(header)
    log.info("\n%s\n%s", header, separator)

    while time.monotonic() < end_time:
        sleep_for = min(interval_s, max(0.0, end_time - time.monotonic()))
        time.sleep(sleep_for)

        if time.monotonic() >= end_time:
            break

        snapshot_num += 1
        elapsed = int(duration_s - (end_time - time.monotonic()))

        # Flow metrics
        freq = snappi.MetricsRequest()
        freq.choice = freq.FLOW
        fres = api.get_metrics(freq)

        # Port metrics
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
                "%8d  %-20s  %14d  %14d  %8.4f  %14.1f",
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
                "link": getattr(pm, "link", "unknown"),
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
    log.info("Metrics collection complete (%d snapshots).", snapshot_num)
    return snapshots


# ===========================================================================
# ASSERTION VALIDATORS
# ===========================================================================


def _assert_bgp_peers_up(
    api: snappi.Api,
    peer_names: list[str],
) -> list[dict[str, Any]]:
    """Assert that each named BGP peer is in the 'up' or 'established' state."""
    states = _get_bgpv4_states(api)
    results: list[dict[str, Any]] = []

    for name in peer_names:
        state = states.get(name, "not_found")
        passed = state in ("up", "established")
        status = "PASS" if passed else "FAIL"
        log.info(
            "[Assertion] bgp_peer_up(%s): %s  (state=%s)",
            name,
            status,
            state,
        )
        results.append(
            {
                "name": f"bgp_peer_up_{name}",
                "type": "bgp_state",
                "peer": name,
                "expected": "up",
                "actual": state,
                "passed": passed,
            }
        )

    return results


def _assert_flow_metrics(
    api: snappi.Api,
    flow_name: str,
) -> list[dict[str, Any]]:
    """
    Validate three assertions on the named flow:
      1. frames_tx > 0
      2. frames_rx > 0
      3. frames_tx == frames_rx  (zero loss)
    """
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    metrics_by_name = {fm.name: fm for fm in res.flow_metrics}
    results: list[dict[str, Any]] = []

    if flow_name not in metrics_by_name:
        msg = f"Flow '{flow_name}' not found in metrics response"
        log.error("[Assertion] %s: FAIL  (%s)", flow_name, msg)
        results.append(
            {
                "name": f"flow_{flow_name}",
                "type": "flow_metrics",
                "flow": flow_name,
                "passed": False,
                "error": msg,
            }
        )
        return results

    fm = metrics_by_name[flow_name]
    tx = int(fm.frames_tx)
    rx = int(fm.frames_rx)
    loss = tx - rx
    loss_pct = (loss / tx * 100.0) if tx > 0 else 0.0

    # Assertion 1: frames_tx > 0
    tx_passed = tx > 0
    log.info(
        "[Assertion] %s frames_tx > 0: %s  (tx=%d)",
        flow_name,
        "PASS" if tx_passed else "FAIL",
        tx,
    )
    results.append(
        {
            "name": f"{flow_name}_frames_tx_gt_0",
            "type": "flow_frames_tx",
            "flow": flow_name,
            "expected": "> 0",
            "actual": tx,
            "passed": tx_passed,
        }
    )

    # Assertion 2: frames_rx > 0
    rx_passed = rx > 0
    log.info(
        "[Assertion] %s frames_rx > 0: %s  (rx=%d)",
        flow_name,
        "PASS" if rx_passed else "FAIL",
        rx,
    )
    results.append(
        {
            "name": f"{flow_name}_frames_rx_gt_0",
            "type": "flow_frames_rx",
            "flow": flow_name,
            "expected": "> 0",
            "actual": rx,
            "passed": rx_passed,
        }
    )

    # Assertion 3: frames_tx == frames_rx (zero loss)
    zero_loss = loss == 0
    log.info(
        "[Assertion] %s zero_loss: %s  (tx=%d, rx=%d, lost=%d, loss=%.6f%%)",
        flow_name,
        "PASS" if zero_loss else "FAIL",
        tx,
        rx,
        loss,
        loss_pct,
    )
    results.append(
        {
            "name": f"{flow_name}_zero_loss",
            "type": "flow_loss",
            "flow": flow_name,
            "frames_tx": tx,
            "frames_rx": rx,
            "frames_lost": loss,
            "loss_pct": round(loss_pct, 6),
            "passed": zero_loss,
        }
    )

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
    Execute the 2xIxia + FRR DUT BGP routing test.
    Returns True if all assertions pass, False otherwise.
    """
    log.info("=" * 70)
    log.info("Test       : %s", TEST_NAME)
    log.info("Controller : %s  (primary; IXIA_Z at %s)", CONTROLLER_A_URL, CONTROLLER_Z_URL)
    log.info("Duration   : %d s  |  Metrics interval: %d s", TEST_DURATION_S, METRICS_INTERVAL_S)
    log.info("BGP timeout: %d s", BGP_CONVERGENCE_TIMEOUT_S)
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
        # Step 1: Connect to controller A (Snappi dispatches to Z via config)
        # ------------------------------------------------------------------
        api = _connect(CONTROLLER_A_URL)

        # ------------------------------------------------------------------
        # Step 2: Push OTG config (both controllers receive their sub-config)
        # ------------------------------------------------------------------
        _push_config(api)

        # ------------------------------------------------------------------
        # Step 3: Start protocols on both ixia-c instances
        # ------------------------------------------------------------------
        _start_protocols(api)
        protocols_started = True

        # ------------------------------------------------------------------
        # Step 4: Poll until both BGP peers (IXIA_A and IXIA_Z) are up
        # ------------------------------------------------------------------
        bgp_converged = _wait_for_bgp(
            api,
            peer_names=EXPECTED_BGP_PEER_NAMES,
            timeout_s=BGP_CONVERGENCE_TIMEOUT_S,
            poll_s=BGP_CONVERGENCE_POLL_S,
        )

        if not bgp_converged:
            log.error(
                "BGP did not converge within %d s. "
                "Recording failed assertions and skipping traffic.",
                BGP_CONVERGENCE_TIMEOUT_S,
            )
            # Capture final BGP state as failed assertions
            all_assertions.extend(
                _assert_bgp_peers_up(api, EXPECTED_BGP_PEER_NAMES)
            )
            # Record flow assertions as failed (no traffic ran)
            all_assertions.append(
                {
                    "name": f"{FLOW_UNDER_TEST}_skipped",
                    "type": "flow_metrics",
                    "flow": FLOW_UNDER_TEST,
                    "passed": False,
                    "error": "Traffic skipped due to BGP convergence failure",
                }
            )

        else:
            # --------------------------------------------------------------
            # Step 5: Start traffic
            # --------------------------------------------------------------
            _start_traffic(api)
            traffic_started = True

            # --------------------------------------------------------------
            # Step 6: Collect metrics every 5 s for 60 s
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
            # Step 7: Stop traffic programmatically (continuous duration)
            # --------------------------------------------------------------
            _stop_traffic(api)
            traffic_started = False

            # --------------------------------------------------------------
            # Step 8: Collect final BGP state and flow metrics
            # --------------------------------------------------------------
            log.info("-" * 70)
            log.info("Validating assertions...")

            # BGP session state assertions
            all_assertions.extend(
                _assert_bgp_peers_up(api, EXPECTED_BGP_PEER_NAMES)
            )

            # Flow metric assertions (tx > 0, rx > 0, tx == rx)
            all_assertions.extend(
                _assert_flow_metrics(api, FLOW_UNDER_TEST)
            )

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
        # Cleanup — always runs even on error or keyboard interrupt
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
        "controller_a": CONTROLLER_A_URL,
        "controller_z": CONTROLLER_Z_URL,
        "topology": "2xIxia + FRR DUT (eBGP routing)",
        "started_at": started_at,
        "finished_at": finished_at,
        "test_duration_s": TEST_DURATION_S,
        "metrics_interval_s": METRICS_INTERVAL_S,
        "bgp_convergence_timeout_s": BGP_CONVERGENCE_TIMEOUT_S,
        "bgp_peers_monitored": EXPECTED_BGP_PEER_NAMES,
        "flow_under_test": FLOW_UNDER_TEST,
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
