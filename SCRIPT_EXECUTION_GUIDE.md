# Snappi Test Script Execution Guide

**Script:** `test_bgp_convergence.py`
**Test Type:** BGP Convergence with Bidirectional Traffic (CP+DP)
**Status:** ✅ Ready to Execute
**Generated:** 2026-03-19

---

## Quick Start

```bash
# Step 1: Install Snappi SDK
pip install snappi

# Step 2: Ensure Ixia-c is deployed and healthy
./setup-ixia-c-bgp.sh
# OR verify manually:
docker compose -f docker-compose-bgp-cpdp.yml ps
curl -sk https://localhost:8443/config

# Step 3: Run the test
python test_bgp_convergence.py
```

---

## Detailed Execution Steps

### Prerequisites

1. **Ixia-c Infrastructure Deployed:**
   ```bash
   docker compose -f docker-compose-bgp-cpdp.yml ps
   ```
   Expected output:
   ```
   NAME                                    STATUS
   keng-controller                         Up
   ixia-c-traffic-engine-veth-a           Up
   ixia-c-traffic-engine-veth-z           Up
   ixia-c-protocol-engine-veth-a          Up
   ixia-c-protocol-engine-veth-z          Up
   ```

2. **Snappi SDK Installed:**
   ```bash
   pip install snappi
   python -c "import snappi; print(f'Snappi {snappi.__version__} installed')"
   ```

3. **Controller Reachable:**
   ```bash
   curl -sk https://localhost:8443/config
   # Should return: {}
   ```

### Run the Test

```bash
python test_bgp_convergence.py
```

### Expected Output

```
===============================================================================================
  Snappi BGP Convergence Test (CP+DP)
  Controller: https://localhost:8443
  Test: BGP AS 65001 ↔ AS 65002 with bidirectional traffic
===============================================================================================

[Connecting] API endpoint: https://localhost:8443
  [Attempt 1/3] Connecting...
  ✓ Connected successfully

[Step 1/7] Loading OTG configuration...
  Config structure:
    - Ports: 2
    - Devices: 2
    - Flows: 2
  Pushing config to controller...
  ✓ Configuration loaded and validated

[Step 2/7] Waiting for BGP convergence (max 30s)...
  [1s] BGP sessions: 0 up, 0 down
  [2s] BGP sessions: 0 up, 0 down
  ...
  [25s] BGP sessions: 2 up, 0 down
  ✓ BGP converged in 25s (2 sessions established)

[Step 3/7] Starting traffic transmission...
  ✓ Traffic started

  ⏸ Press Enter to START TRAFFIC (Ctrl+C to abort)...
[Enter pressed]

  ✓ Traffic started

[Step 4/7] Collecting metrics (every 5s for 120s)...
  ----------------------------------------------------------------------------------------------------
  Time (s)     | TxFrames        | RxFrames        | Loss %     | Pps
  ----------------------------------------------------------------------------------------------------
  5            | 10000           | 10000           | 0.00       | 2000
  10           | 20000           | 20000           | 0.00       | 2000
  15           | 30000           | 30000           | 0.00       | 2000
  ...
  120          | 240000          | 240000          | 0.00       | 2000
  ----------------------------------------------------------------------------------------------------
  ✓ Metrics collection complete

[Step 5/7] Validating assertions...
  BGP Convergence                | Expected: Established | Actual: Established | ✓ PASS
  Packet Loss                    | Expected: < 0.1% | Actual: 0.00% | ✓ PASS
  Frames Transmitted             | Expected: > 90000 | Actual: 240000 | ✓ PASS

  Overall Result                 | ✓ ALL PASSED

[Step 6/7] Stopping traffic...
  ✓ Traffic stopped

[Step 7/7] Saving test report...
  ✓ Report saved: test_report_bgp_20260319_153045.json

===============================================================================================
  ✓ TEST PASSED
===============================================================================================
```

---

## Script Phases

### Phase 1: Connection (Automatic)
- Connects to controller at https://localhost:8443
- Retries up to 3 times with exponential backoff
- Status: ✓ Automatic

### Phase 2: Config Loading (Automatic)
- Loads OTG configuration (embedded in script)
- Validates ports, devices, flows
- Pushes config to controller
- Status: ✓ Automatic

### Phase 3: BGP Convergence (Automatic)
- Waits for BGP sessions to reach **Established** state
- Polls every 1 second (max 30 seconds)
- Expected: 2 BGP sessions (device1 ↔ device2)
- Status: ✓ Automatic

### Phase 4: Traffic Start (Interactive)
- Prompts user to press Enter before starting traffic
- Allows time to verify BGP convergence
- Status: ⏸ **User Confirmation Required**

### Phase 5: Metrics Collection (Automatic)
- Collects port and flow statistics
- Polls every 5 seconds for 120 seconds
- Displays real-time metrics table
- Calculates: TX frames, RX frames, packet loss %, rate (pps)
- Status: ✓ Automatic

### Phase 6: Assertions (Automatic)
- Validates 3 assertions:
  1. **BGP Convergence** — Sessions should be Established ✓
  2. **Packet Loss** — Should be < 0.1% ✓
  3. **Frames** — Should transmit > 90,000 frames ✓
- Status: ✓ Automatic

### Phase 7: Cleanup & Report (Automatic)
- Stops traffic
- Saves JSON report with all metrics
- Status: ✓ Automatic

---

## Test Execution Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| **1. Connection** | ~2-5s | Connect to controller (with retries) |
| **2. Config Load** | ~2s | Load OTG config, push to controller |
| **3. BGP Convergence** | ~20-30s | Wait for BGP Established state |
| **4. User Prompt** | Variable | Press Enter to start traffic |
| **5. Traffic & Metrics** | 120s | Run traffic, collect metrics every 5s |
| **6. Assertions** | ~1s | Validate test results |
| **7. Cleanup** | ~2s | Stop traffic, save report |
| **TOTAL** | ~150-170s | ~2.5-3 minutes end-to-end |

---

## Expected Assertions & Results

### Assertion 1: BGP Convergence ✓

```
Expected: BGP sessions reach "Established" state
Actual: 2 sessions established (device1 ↔ device2)
Status: ✓ PASS
```

**BGP convergence typically takes 20-30 seconds.** If it takes longer:
- Check controller logs: `docker logs keng-controller`
- Verify protocol engines are running: `docker compose ps`
- Check veth injection: `docker exec ixia-c-traffic-engine-veth-a ip link show`

### Assertion 2: Packet Loss ✓

```
Expected: Packet loss < 0.1%
Actual: 0.00% (zero loss)
Status: ✓ PASS
```

**Zero packet loss is expected** after BGP convergence. If there's loss:
- Ensure BGP is fully converged before traffic starts
- Check port connectivity: `docker exec ixia-c-traffic-engine-veth-a ip link show veth-a`
- Verify flow configuration in OTG JSON

### Assertion 3: Frames Transmitted ✓

```
Expected: Frames transmitted > 90,000
Actual: 240,000 frames (120 seconds @ 1000 pps both flows)
Status: ✓ PASS
```

**Script runs for 120 seconds with 2 bidirectional flows at 1000 pps each:**
- Flow 1 (te1→te2): 120,000 packets
- Flow 2 (te2→te1): 120,000 packets
- Total: 240,000 packets

---

## JSON Report Output

The script generates a JSON report file: `test_report_bgp_YYYYMMDD_HHMMSS.json`

### Report Structure

```json
{
  "timestamp": "2026-03-19T15:30:45.123456",
  "controller": "https://localhost:8443",
  "test_type": "BGP Convergence",
  "duration_seconds": 120,
  "bgp_converged": true,
  "assertions": {
    "bgp_convergence": {
      "expected": "Established",
      "actual": "Established",
      "passed": true
    },
    "packet_loss": {
      "expected": "< 0.1%",
      "actual": "0.00%",
      "passed": true
    },
    "frames_transmitted": {
      "expected": "> 90000",
      "actual": 240000,
      "passed": true
    }
  },
  "overall_result": "PASSED",
  "metrics": [
    {
      "elapsed": 5,
      "tx_frames": 10000,
      "rx_frames": 10000,
      "loss_frames": 0,
      "loss_pct": 0.0,
      "rate_pps": 2000.0
    },
    ...
  ]
}
```

### Reading the Report

```bash
# Pretty-print the report
cat test_report_bgp_*.json | jq .

# Extract assertion results
cat test_report_bgp_*.json | jq '.assertions'

# Extract overall result
cat test_report_bgp_*.json | jq '.overall_result'

# Extract final metrics
cat test_report_bgp_*.json | jq '.metrics[-1]'
```

---

## Troubleshooting

### Issue: Connection Refused (https://localhost:8443)

**Symptom:**
```
✗ Connection failed: [Errno 111] Connection refused
✗ Failed after 3 attempts
```

**Causes:**
1. Ixia-c not deployed
2. Controller container crashed
3. Wrong IP/port

**Solutions:**
```bash
# Verify deployment
docker compose -f docker-compose-bgp-cpdp.yml ps

# Check logs
docker logs keng-controller

# Restart if needed
docker compose -f docker-compose-bgp-cpdp.yml restart keng-controller
```

---

### Issue: BGP Convergence Timeout

**Symptom:**
```
[30s] BGP sessions: 0 up, 0 down
⚠ BGP convergence timeout (30s) - proceeding with traffic
```

**Causes:**
1. Veth not injected into containers
2. Protocol engines not started
3. BGP configuration incorrect

**Solutions:**
```bash
# Check veth in TE-A namespace
docker exec ixia-c-traffic-engine-veth-a ip link show
# Should show: veth-a

# Check protocol engine logs
docker logs ixia-c-protocol-engine-veth-a

# Re-run setup script
./setup-ixia-c-bgp.sh
```

---

### Issue: Packet Loss

**Symptom:**
```
Packet Loss | Expected: < 0.1% | Actual: 45.50% | ✗ FAIL
```

**Causes:**
1. BGP not fully converged when traffic starts
2. Interface issues (veth not properly configured)
3. Resource constraints

**Solutions:**
```bash
# Increase BGP convergence timeout in script (line: BGP_CONVERGENCE_TIMEOUT = 30)
BGP_CONVERGENCE_TIMEOUT = 60  # Increase to 60 seconds

# Verify interface is up
docker exec ixia-c-traffic-engine-veth-a ip link show veth-a
# Should show: state UP

# Check traffic engine logs
docker logs ixia-c-traffic-engine-veth-a
```

---

## Customization

### Change Test Duration

Edit line in `test_bgp_convergence.py`:
```python
TEST_DURATION = 120  # Change to desired duration (seconds)
```

### Change Metrics Interval

Edit line in `test_bgp_convergence.py`:
```python
METRICS_INTERVAL = 5  # Change to desired interval (seconds)
```

### Change Traffic Rate

Edit OTG config in script (search for `"pps": 1000`):
```json
"rate": {
  "choice": "pps",
  "pps": 5000  # Change to desired rate
}
```

### Change Assertion Thresholds

Edit ASSERTIONS dict in script:
```python
ASSERTIONS = {
    "packet_loss": {
        "max_loss_percent": 0.5,  # Increase tolerance
        "operator": "less_than"
    }
}
```

---

## CI/CD Integration

### Run in Non-Interactive Mode (No Prompts)

Modify the script to comment out the input() line:

```python
# input(f"\n  ⏸ Press Enter to START TRAFFIC (Ctrl+C to abort)...")
# start_traffic(api)
```

Or run with stdin redirect:
```bash
echo "" | python test_bgp_convergence.py
```

### Capture Results for CI/CD

```bash
# Run test
python test_bgp_convergence.py

# Check exit code
if [ $? -eq 0 ]; then
  echo "Test PASSED"
else
  echo "Test FAILED"
fi

# Extract metrics
python -c "
import json
import glob

# Find latest report
reports = glob.glob('test_report_bgp_*.json')
latest = max(reports)

with open(latest) as f:
    data = json.load(f)
    print(f\"Result: {data['overall_result']}\")
    print(f\"BGP Converged: {data['bgp_converged']}\")
"
```

---

## Files Reference

| File | Purpose |
|------|---------|
| **test_bgp_convergence.py** | Main test script (standalone, executable) |
| **infrastructure.yaml** | Infrastructure configuration (referenced for documentation) |
| **bgp_convergence_cpdp.json** | OTG configuration (embedded in script) |
| **docker-compose-bgp-cpdp.yml** | Ixia-c deployment (must be running) |
| **test_report_bgp_*.json** | Generated test reports (one per run) |

---

## Support & Next Steps

If test passes:
```bash
✓ BGP convergence working
✓ Bidirectional traffic flowing
✓ Zero packet loss achieved

Next: Scale up with more ports, protocols, or flows
```

If test fails:
```bash
1. Check Ixia-c deployment: docker compose ps
2. Review controller logs: docker logs keng-controller
3. Inspect protocol state: docker exec <container> <command>
4. Re-run setup: ./setup-ixia-c-bgp.sh
```

---

**Script Status:** ✅ Ready for Execution
**Generated:** 2026-03-19
**Version:** 1.0
