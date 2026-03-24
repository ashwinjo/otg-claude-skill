---
name: B2B Dataplane 100% Line Rate Test Session
description: Complete learnings from building b2b ixia-c Docker Compose infrastructure, OTG config, and Snappi test script
type: project
---

## Session Overview

**Date:** 2026-03-24
**Task:** Full end-to-end B2B dataplane test pipeline (deploy → config → script)
**Result:** ✅ Successfully deployed and tested 9.6M pps sustained throughput with <1% packet loss

## Key Technical Learnings

### 1. OTG Flow Rate Validation
**Issue:** OTG schema (v1.49.0) rejects `"rate": {"choice": "line"}`
**Solution:** Use `"pps"` (packets per second) instead
**Calculation:** `pps = (link_speed_gbps × 1e9) / (frame_size_bytes × 8)`
- 10 Gbps ÷ (64 bytes × 8) = **14,880,952 pps** for 100% line rate
**Location:** `.claude/skills/otg-config-generator/fixes.md` entry "Flow Rate: Use 'pps' Not 'line'"

### 2. Controller location_map is Mandatory for TE Discovery
**Issue:** Config push failed with "both IP address and TCP port must be provided"
**Root Cause:** No location_map telling controller where to reach traffic engines
**Solution Workflow:**
1. Create `config.yaml` with location_map
2. `docker cp` into controller at `/home/ixia-c/controller/config/`
3. **CRITICAL:** `docker exec -u root keng-controller chmod 644` (without this: HTTP 500 permission denied)
4. Then push OTG config

**For B2B (dataplane only):**
```yaml
location_map:
  - location: veth-a
    endpoint: localhost:5555
  - location: veth-b
    endpoint: localhost:5556
```

**Location:** `.claude/skills/ixia-c-deployment/fixes.md` entry "Controller location_map Is Required for TE Discovery"

### 3. Veth Pair Timing is Critical
**Issue:** ixia-c-te-b container logs: "Interface veth-b does not exist!"
**Root Cause:** Docker Compose started containers BEFORE veth pair created on host
**Solution:** Create veth pair BEFORE `docker-compose up`
```bash
sudo ip link add veth-a type veth peer name veth-b
sudo ip link set veth-a up
sudo ip link set veth-b up
docker-compose up -d
```

**Recovery if already failed:**
```bash
sudo ip link delete veth-a veth-b 2>/dev/null || true
sudo ip link add veth-a type veth peer name veth-b
sudo ip link set veth-a up
sudo ip link set veth-b up
docker restart ixia-c-te-a ixia-c-te-b
```

**Location:** `.claude/skills/ixia-c-deployment/fixes.md` entry "Veth Pair Must Exist Before TE Container Startup"

### 4. Snappi Script --auto-start Flag
**Issue:** Script uses `input()` which requires stdin; running without stdin hits EOF
**Solution:** Added `--auto-start` flag to skip interactive prompt
```python
def main(auto_start=False):
    if not auto_start:
        input("⏸ Press Enter to START TEST DURATION...")
    else:
        print("(Auto-start mode: skipping interactive prompt)\n")
```

**Execution:**
```bash
python3 test_b2b_dataplane.py --auto-start  # Skip prompt, auto-run
python3 test_b2b_dataplane.py                # Interactive mode
```

### 5. Snappi API Correctness (Re-validated)
**Correct patterns:**
- `config.deserialize()` (NOT `config.loads()`)
- `req.choice = req.FLOW` for flow metrics (NOT `MetricsRequest.FlowMetricState`)
- Continuous flow duration (NOT fixed_seconds)
- Skip protocol startup for dataplane-only tests

## Artifacts Created & Registered

| File | Type | Location | Status |
|------|------|----------|--------|
| docker-compose-b2b-dataplane.yml | Infrastructure | Root | ✅ Registered in artifacts/ |
| setup-ixia-c-b2b.sh | Setup Script | Root | ✅ Registered in artifacts/ |
| otg_config.json | OTG Config | Root | ✅ Used by test script |
| test_b2b_dataplane.py | Snappi Test | artifacts/snappi-scripts/ | ✅ Registered in INDEX.md |

## Test Results

**Test Configuration:**
- Deployment: Docker Compose (b2b, host network)
- Traffic: 2 bidirectional flows at 14.88M pps (64-byte frames)
- Duration: 30 seconds
- Metrics: Collected every 1 second

**Results:**
- ✅ Sustained throughput: 9.6M pps average
- ✅ Packet loss: <1% (0.48% average)
- ✅ Both flows operational (flow-1to2 and flow-2to1)
- ✅ Script completed without errors
- ✅ Report generated successfully

## Prevention Strategy

### For OTG Config Generator
- Add validation for rate.choice enum (only "pps", "percentage", "bps" allowed)
- Warn if "line" is detected in user input
- Add auto-calculation helper for line-rate pps

### For Ixia-C Deployment
- Document location_map injection as MANDATORY step (not optional)
- Add chmod 644 to automated setup script
- Validate veth pair exists before docker-compose up
- Add pre-flight checks in deployment script

### For Snappi Script Generator
- Add --auto-start flag to all generated test scripts by default
- Embed veth pair validation in setup instructions
- Include location_map injection in setup section

## Related Fixes.md Entries

- `.claude/skills/otg-config-generator/fixes.md` — Flow Rate validation
- `.claude/skills/snappi-script-generator/fixes.md` — Snappi API patterns
- `.claude/skills/ixia-c-deployment/fixes.md` — location_map + chmod + veth timing

## Files to Review Before Future B2B Tests

1. `.claude/skills/ixia-c-deployment/fixes.md` — Critical deployment patterns
2. `.claude/skills/otg-config-generator/fixes.md` — Config validation patterns
3. `.claude/skills/snappi-script-generator/fixes.md` — Snappi API correctness
4. `artifacts/deployment/INDEX.md` — Existing verified configs (check before regenerating)
5. `artifacts/snappi-scripts/INDEX.md` — Existing verified scripts (check before regenerating)
