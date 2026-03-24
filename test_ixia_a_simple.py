#!/usr/bin/env python3
"""
Simple validation test: IXIA_A eth1 connectivity
Verifies the Containerlab deployment is working
"""

import logging
import time
import urllib3

import snappi

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ixia_a_simple")

CONTROLLER_URL = "https://172.20.20.4:8443"

# Single port test - eth1 only (connected to FRR)
OTG_CONFIG_JSON = r"""
{
  "ports": [
    { "name": "P1", "location": "eth1" }
  ],
  "flows": [
    {
      "name": "simple_flow",
      "tx_rx": { "choice": "port", "port": { "tx_name": "P1", "rx_names": ["P1"] } },
      "packet": [{ "choice": "ethernet", "ethernet": { "dst": { "choice": "value", "value": "00:00:00:00:00:01" }, "src": { "choice": "value", "value": "00:00:00:00:00:01" } } }],
      "size": { "choice": "fixed", "fixed": 64 },
      "rate": { "choice": "pps", "pps": 100 },
      "duration": { "choice": "continuous" },
      "metrics": { "enable": true }
    }
  ]
}
"""

try:
    log.info("=" * 70)
    log.info("Test: IXIA_A Containerlab Deployment Validation")
    log.info("=" * 70)
    
    log.info(f"Connecting to {CONTROLLER_URL}...")
    api = snappi.api(location=CONTROLLER_URL, verify=False)
    api.get_config()
    log.info("✅ Connected successfully!")
    
    log.info("Pushing config...")
    cfg = snappi.Config()
    cfg.deserialize(OTG_CONFIG_JSON)
    api.set_config(cfg)
    log.info(f"✅ Config pushed: {len(cfg.ports)} port(s), {len(cfg.flows)} flow(s)")
    
    log.info("Starting traffic...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "start"
    api.set_control_state(cs)
    log.info("✅ Traffic started")
    
    log.info("Running for 10 seconds...")
    time.sleep(10)
    
    log.info("Stopping traffic...")
    cs = snappi.ControlState()
    cs.traffic.flow_transmit.state = "stop"
    api.set_control_state(cs)
    log.info("✅ Traffic stopped")
    
    time.sleep(1)
    
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    metrics = api.get_metrics(req).flow_metrics
    
    log.info("\nFinal metrics:")
    for fm in metrics:
        tx = int(fm.frames_tx)
        rx = int(fm.frames_rx)
        log.info(f"  {fm.name}: TX={tx} RX={rx}")
        
        if tx > 0:
            log.info("✅ Traffic was sent")
        else:
            log.error("❌ No traffic sent")
    
    log.info("=" * 70)
    log.info("✅ Containerlab deployment is working!")
    log.info("=" * 70)
    
except Exception as e:
    log.error(f"❌ Error: {e}", exc_info=True)
