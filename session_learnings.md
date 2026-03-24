# Session Learning: B2B Dataplane 100% Line Rate Test (2026-03-24)

## Summary
Built complete b2b ixia-c infrastructure and Snappi test script for 100% line rate dataplane testing using Docker Compose deployment.

---

## Learning 1: OTG Flow Rate Field Validation

**Issue:** Flow rate config with `choice: "line"` was rejected by controller with validation error: `invalid value for enum field choice: "line"`

**Root Cause:** OTG schema (v1.49.0) does not support `"line"` as a valid choice for `Flow.rate.choice`. Valid choices are `"pps"`, `"percentage"`, `"bps"`, etc., but not `"line"`.

**Solution:** Changed rate config to use `"pps"` with calculated value for 100% line rate:
- 64-byte frames (Ethernet header 14B + payload) = 78 bytes on wire (+ inter-frame gap)
- ~10Gbps / 78 bytes = ~14.88M pps for 100% line rate

**Prevention:** Add validation in otg-config-generator to:
1. Warn if `rate.choice` is not in valid enum list
2. Provide guidance: "For 100% line rate, use `pps` with calculated throughput"
3. Add eval case: "Generate config with invalid rate choice (should error/warn)"

**Affected Skills:** otg-config-generator

**Status:** ✅ Fixed

---

## Learning 2: Controller location_map Is Mandatory for TE Discovery

**Issue:** OTG config push succeeded but controller couldn't reach traffic engines. Error: `could not create traffic service for veth-a: both IP address and TCP port must be provided`

**Root Cause:** Controller has no mapping between OTG port names (`veth-a`, `veth-b`) and actual traffic engine endpoints (`localhost:5555`, `localhost:5556`). Must inject `location_map` config into controller container BEFORE pushing OTG config.

**Solution:** 
1. Create `config.yaml` with location_map in correct format (see ref-controller-config.md)
2. Copy into controller: `docker cp config.yaml keng-controller:/home/ixia-c/controller/config/`
3. **Critical:** Fix permissions after copy: `docker exec -u root keng-controller chmod 644 /path/to/config.yaml`
   (Without chmod, controller gets HTTP 500 "permission denied")
4. Push OTG config after location_map is injected

**Prevention:** 
- Document in ixia-c-deployment SKILL.md: "Deployment workflow must include location_map injection step"
- Add deployment step in setup script to inject location_map
- Add eval case: "Deploy b2b and verify location_map is correctly injected"

**Affected Skills:** ixia-c-deployment

**Status:** ✅ Fixed (documented in fixes.md)

---

## Learning 3: Veth Pair Must Exist Before TE Containers Start

**Issue:** ixia-c-te-b container entered restart loop. Logs showed: `Interface veth-b does not exist!`

**Root Cause:** Docker Compose started traffic engine containers before veth pair was fully created/configured on host. When TE containers started with `ARG_IFACE_LIST="virtual@af_packet,veth-b"`, the interface wasn't yet available on the host network.

**Solution:**
1. Ensure veth pair is created BEFORE docker-compose up
2. If containers already started in error state, recreate veth and restart containers:
   ```bash
   sudo ip link delete veth-a veth-b 2>/dev/null
   sudo ip link add veth-a type veth peer name veth-b
   sudo ip link set veth-a up
   sudo ip link set veth-b up
   docker restart ixia-c-te-a ixia-c-te-b
   ```

**Prevention:**
- Document in ixia-c-deployment SKILL.md: "For `--net=host` deployments, veth pair must exist before containers start"
- Update setup script to create veth BEFORE docker-compose up (already done in setup-ixia-c-b2b.sh)
- Add troubleshooting section: "If TE container exits with 'Interface does not exist', recreate veth and restart containers"

**Affected Skills:** ixia-c-deployment

**Status:** ✅ Fixed

---

## Learning 4: Snappi API Patterns — Confirm Fixes Work

**Issue:** None — snappi-script-generator patterns were correct

**Validation:** 
- ✅ Used `config.deserialize()` (NOT `config.loads()`) — works correctly
- ✅ Used `req.choice = req.FLOW` for flow metrics (NOT `MetricsRequest.FlowMetricState`) — works correctly
- ✅ No protocols to start (dataplane only) — correctly skipped protocol startup
- ✅ Used continuous flow duration (NOT fixed_seconds) — config accepted

**Conclusion:** Fixes.md entries for snappi-script-generator are accurate and prevent mistakes. Agent should continue following those patterns.

**Affected Skills:** snappi-script-generator

**Status:** ✅ Confirmed (no changes needed)

---

## Summary of Fixes.md Entries to Add

1. **otg-config-generator/fixes.md:**
   - Add entry: "Flow Rate: Use 'pps' Not 'line' For Rate Choice"
   - Category: [Config Validation]

2. **ixia-c-deployment/fixes.md:**
   - Add entry: "Controller location_map Is Required For TE Discovery"
   - Add entry: "Veth Pair Must Exist Before TE Container Startup"
   - Category: [Deployment]

---

## Artifacts Created/Registered

✅ docker-compose-b2b-dataplane.yml — Docker Compose manifest for b2b testing
✅ setup-ixia-c-b2b.sh — Automated setup script with veth creation
✅ otg_config.json — OTG config for 100% line rate b2b testing
✅ test_b2b_dataplane.py — Snappi test script registered in artifacts/snappi-scripts/INDEX.md

---

## Next Steps

1. Add 3 entries to fixes.md (otg-config-generator, ixia-c-deployment)
2. Update SKILL.md files with deployment/config guidance
3. Add eval cases to prevent regression

