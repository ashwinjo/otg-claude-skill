---
name: Proven working Snappi script patterns
description: Validated Snappi API patterns drawn from scripts that ran successfully against ixia-c keng-controller — use these as the structural template for all generated scripts
type: reference
---

The following patterns are taken from scripts validated in production against ixia-c Docker Compose
and Containerlab deployments (keng-controller v1.48.0-5 and Docker Compose variants).

## Connection
```python
api = snappi.api(location=CONTROLLER_URL, verify=False)
api.get_config()  # connectivity probe — fails fast if unreachable
```

## Config push — use deserialize(), not loads()
```python
cfg = snappi.Config()
cfg.deserialize(OTG_CONFIG_JSON)   # NOT cfg.loads() — that method does not exist
api.set_config(cfg)
```

## Traffic start/stop — use flow_transmit.state string
```python
cs = snappi.ControlState()
cs.traffic.flow_transmit.state = "start"   # or "stop"
api.set_control_state(cs)
```

## Metrics — use req.choice, not req.flow.state pattern
```python
req = snappi.MetricsRequest()
req.choice = req.FLOW   # or req.PORT
result = api.get_metrics(req)
for fm in result.flow_metrics:
    tx = int(fm.frames_tx)
    rx = int(fm.frames_rx)
```

## ixia-c-one OTG config restrictions (enforced in all generated configs)
- No `metrics.latency` or `metrics.loss` fields — not supported
- No `metrics.timestamps` field — strip before push
- Duration must be `{"choice": "continuous"}` — fixed_seconds crashes controller
- Traffic stopped programmatically via set_control_state after desired duration

## Script structure validated by test_b2b_loopback_clab.py and test_b2b_dataplane_10gbps.py
1. `_connect()` — retry with exponential backoff (1s, 2s, 4s)
2. `_push_config()` — deserialize + set_config
3. `_start_traffic()` — flow_transmit state = start
4. `_poll_metrics()` — loop printing table, collect snapshots
5. `_stop_traffic()` — flow_transmit state = stop
6. `time.sleep(1)` — settle delay for controller to flush counters
7. `_collect_final_metrics()` — one final snapshot for assertions
8. `_run_assertions()` — per-flow checks, bidirectional check
9. `_clear_config()` — push empty Config() on exit (cleanup)
10. `_save_report()` — JSON report with timestamp

## Throughput calculation (wire rate, 64-byte frames)
```python
WIRE_FRAME_BYTES = 84  # 64 payload + 20 overhead (preamble + SFD + IFG)
rx_mbps = (frames * WIRE_FRAME_BYTES * 8) / duration_s / 1_000_000
rx_gbps = rx_mbps / 1000
line_pct = (rx_gbps / link_speed_gbps) * 100
```

## Reference scripts in repo
- `/home/ubuntu/otg-claude-skill/test_b2b_loopback_clab.py` — pure Ethernet, 1000 pps, Containerlab veth
- `/home/ubuntu/otg-claude-skill/test_b2b_dataplane_10gbps.py` — Eth/IPv4/UDP, 100% line rate, Docker Compose
