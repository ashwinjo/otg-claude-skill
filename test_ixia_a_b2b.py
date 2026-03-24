#!/usr/bin/env python3
"""
IXIA_A B2B Loopback Test — ixia-frr Containerlab Deployment
===========================================================
Test a single ixia-c-one node from the 2xIxia+FRR Containerlab deployment
in B2B loopback mode (eth1 ↔ eth2)
"""

import json
import logging
import sys
import time
import urllib3
from datetime import datetime, timezone

import snappi

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ixia_a_b2b_loopback")

CONTROLLER_URL = "https://172.20.20.4:8443"
TEST_NAME = "ixia_a_b2b_loopback"
TEST_DURATION_S = 30
METRICS_INTERVAL_S = 5

OTG_CONFIG_JSON = r"""
{
  "ports": [
    { "name": "P1", "location": "eth1" },
    { "name": "P2", "location": "eth2" }
  ],
  "flows": [
    {
      "name": "P1_to_P2",
      "tx_rx": { "choice": "port", "port": { "tx_name": "P1", "rx_names": ["P2"] } },
      "packet": [{ "choice": "ethernet", "ethernet": { "dst": { "choice": "value", "value": "00:00:00:00:00:02" }, "src": { "choice": "value", "value": "00:00:00:00:00:01" } } }],
      "size": { "choice": "fixed", "fixed": 64 },
      "rate": { "choice": "pps", "pps": 1000 },
      "duration": { "choice": "continuous" },
      "metrics": { "enable": true }
    },
    {
      "name": "P2_to_P1",
      "tx_rx": { "choice": "port", "port": { "tx_name": "P2", "rx_names": ["P1"] } },
      "packet": [{ "choice": "ethernet", "ethernet": { "dst": { "choice": "value", "value": "00:00:00:00:00:01" }, "src": { "choice": "value", "value": "00:00:00:00:00:02" } } }],
      "size": { "choice": "fixed", "fixed": 64 },
      "rate": { "choice": "pps", "pps": 1000 },
      "duration": { "choice": "continuous" },
      "metrics": { "enable": true }
    }
  ]
}
"""

def _connect(url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"Connecting to {url} (attempt {attempt}/{max_retries})...")
            api = snappi.api(location=url, verify=False)
            api.get_config()
            log.info("Connected successfully.")
            return api
        except Exception as exc:
            if attempt < max_retries:
                wait = 2 ** (attempt - 1)
                log.warning(f"Connection failed ({exc}). Retrying in {wait} s...")
                time.sleep(wait)
            else:
                log.error(f"Could not connect after {max_retries} attempts.")
                raise

def _push_config(api):
    log.info("Pushing OTG configuration...")
    cfg = snappi.Config()
    cfg.deserialize(OTG_CONFIG_JSON)
    api.set_config(cfg)
    log.info(f"Config pushed: {len(cfg.ports)} port(s), {len(cfg.flows)} flow(s).")
    return cfg

def _start_traffic(api):
    log.info("Starting traffic...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("Traffic started.")

def _stop_traffic(api):
    log.info("Stopping traffic...")
    try:
        cs = snappi.ControlState()
        cs.traffic.flow_transmit.state = "stop"
        api.set_control_state(cs)
        log.info("Traffic stopped.")
    except Exception as exc:
        log.warning(f"Error stopping traffic: {exc}")

def run_test():
    log.info("=" * 70)
    log.info(f"Test       : {TEST_NAME}")
    log.info(f"Controller : {CONTROLLER_URL}")
    log.info(f"Topology   : B2B loopback (eth1 ↔ eth2) on IXIA_A")
    log.info(f"Duration   : {TEST_DURATION_S} s")
    log.info("=" * 70)

    api = None
    traffic_started = False
    passed = False

    try:
        api = _connect(CONTROLLER_URL)
        _push_config(api)
        _start_traffic(api)
        traffic_started = True

        log.info(f"Running for {TEST_DURATION_S} s...")
        time.sleep(TEST_DURATION_S)

        _stop_traffic(api)
        traffic_started = False
        time.sleep(1)

        # Collect metrics
        req = snappi.MetricsRequest()
        req.choice = req.FLOW
        metrics = api.get_metrics(req).flow_metrics

        log.info("Final metrics:")
        for fm in metrics:
            tx = int(fm.frames_tx)
            rx = int(fm.frames_rx)
            loss = tx - rx
            log.info(f"  [{fm.name}] TX={tx} RX={rx} Loss={loss} Loss%={loss/tx*100.0 if tx > 0 else 0:.2f}%")

        # Assertions
        log.info("-" * 70)
        all_passed = True
        for fm in metrics:
            tx = int(fm.frames_tx)
            rx = int(fm.frames_rx)
            
            checks = [
                (f"{fm.name}: TX > 0", tx > 0),
                (f"{fm.name}: RX > 0", rx > 0),
                (f"{fm.name}: zero loss", tx == rx),
            ]
            
            for check_name, result in checks:
                status = "PASS" if result else "FAIL"
                log.info(f"[{status}] {check_name}")
                if not result:
                    all_passed = False

        passed = all_passed
        verdict = "PASSED" if passed else "FAILED"
        log.info("=" * 70)
        log.info(f"Test result: {verdict}")
        log.info("=" * 70)

    except Exception as exc:
        log.error(f"Unhandled error: {exc}", exc_info=True)
        passed = False

    finally:
        if api is not None and traffic_started:
            _stop_traffic(api)

    return passed

if __name__ == "__main__":
    passed = run_test()
    sys.exit(0 if passed else 1)
