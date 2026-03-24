---
name: Containerlab B2B Test Session Learning (2026-03-22)
description: Captured learnings from successful Containerlab B2B loopback test deployment and execution
type: project
---

## Summary
Successfully deployed, configured, and executed a B2B loopback traffic test on Containerlab with ixia-c-one container. Test achieved zero packet loss with bidirectional 1000 pps traffic flows over 30 seconds.

## Key Learnings

### 1. ixia-c-one Metric Field Incompatibility (BLOCKING)
- ixia-c-one doesn't support flow-level latency/loss metrics
- Remove unsupported fields before pushing to ixia-c-one; use port-level stats instead
- Fixed in snappi-script-generator; permanent fix in otg-config-generator pending

### 2. Snappi Config.deserialize() vs loads()
- Snappi SDK uses `cfg.deserialize()` not `cfg.loads()`
- Documented in fixes.md and SKILL.md

### 3. Containerlab Controller IP Discovery
- Containerlab runs ixia-c-one on isolated Docker network; localhost doesn't work
- Discover via: `docker inspect clab-<topo>-ixia-c | grep IPAddress`

## Test Results
- P1→P2: 29,952 frames TX/RX, 0 loss (998.4 fps)
- P2→P1: 29,981 frames TX/RX, 0 loss (999.37 fps)
- All 6 assertions passed

## Pending Improvements
- Auto-discover Containerlab controller IP in snappi-script-generator
- Add eval test case for ixia-c-one with latency metrics (should auto-remove)
