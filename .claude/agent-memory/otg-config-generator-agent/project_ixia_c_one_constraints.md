---
name: ixia-c-one metric constraints and config patterns
description: Known limitations and correct OTG config patterns for ixia-c-one (keng-controller v1.48.0-5) deployment
type: project
---

ixia-c-one does NOT support flow-level latency or loss metrics. These must be omitted.

**Why:** ixia-c-one is an all-in-one bundle (CP+DP in single container). Full ixia-c CP+DP deployment supports latency/loss; ixia-c-one does not. Pushing a config with these fields causes immediate rejection from the controller.

**How to apply:** When target is ixia-c-one, generate flows with only `"metrics": {"enable": true}`. Never include `metrics.latency` or `metrics.loss`. Use port-level stats (frames_tx, frames_rx) for packet loss assertion.

Additional constraints for ixia-c-one:
- Use `"duration": {"choice": "continuous"}` — fixed_seconds causes controller crash-restart
- Port location format: `<ip>:<port>+<interface>` (e.g., `172.20.20.4:8443+eth1`)
- BGP passive_mode not needed when peering with a real DUT (only needed for back-to-back ixia-c)
- `as_number` on Bgp.V4Peer = LOCAL AS of this device (not the remote peer's AS)
