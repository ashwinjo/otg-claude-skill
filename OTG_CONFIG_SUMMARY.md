# OTG Configuration: BGP Convergence Test (CP+DP)

**Configuration Status:** ✅ Generated & Validated
**Config File:** `bgp_convergence_cpdp.json`
**Schema Version:** OTG 0.11.0+
**Date Generated:** 2026-03-19

---

## Configuration Overview

This OTG configuration sets up a **BGP convergence test** with:
- **2 ports:** te1 (veth-a) and te2 (veth-z)
- **2 BGP devices:** Device1 (AS 65001) and Device2 (AS 65002)
- **2 flows:** Bidirectional at 1000 pps, 512-byte packets
- **Duration:** 120 seconds (120,000 packets per flow)
- **Assertions:** BGP convergence + zero packet loss

---

## Ports

| Port | Location | Use |
|------|----------|-----|
| **te1** | veth-a | Device1 (BGP AS 65001) |
| **te2** | veth-z | Device2 (BGP AS 65002) |

---

## Devices & BGP Configuration

### Device1 (BGP AS 65001)

**Network Settings:**
- Port: te1 (veth-a)
- MAC: `00:11:22:33:44:55`
- IPv4: `10.0.0.1/24`
- Gateway: `10.0.0.2`
- Router ID: `1.0.0.1`

**BGP Settings:**
- AS Number: **65001** (eBGP)
- Peer Address: `10.0.0.2`
- Peer AS: **65002**
- Unicast: IPv4 enabled

---

### Device2 (BGP AS 65002)

**Network Settings:**
- Port: te2 (veth-z)
- MAC: `00:11:22:33:44:66`
- IPv4: `10.0.0.2/24`
- Gateway: `10.0.0.1`
- Router ID: `2.0.0.1`

**BGP Settings:**
- AS Number: **65002** (eBGP)
- Peer Address: `10.0.0.1`
- Peer AS: **65001**
- Unicast: IPv4 enabled

---

## Traffic Flows

### Flow 1: te1 → te2

| Parameter | Value |
|-----------|-------|
| **Source Port** | te1 (Device1) |
| **Destination Port** | te2 (Device2) |
| **Source IP** | 10.0.0.1 |
| **Destination IP** | 10.0.0.2 |
| **Source MAC** | 00:11:22:33:44:55 |
| **Dest MAC** | 00:11:22:33:44:66 |
| **Protocol** | UDP (src:5000, dst:5001) |
| **Packet Size** | 512 bytes (fixed) |
| **Rate** | 1000 pps |
| **Total Packets** | 120,000 (120 seconds @ 1000 pps) |
| **Expected Frames RX** | 120,000 (after BGP convergence) |

### Flow 2: te2 → te1

| Parameter | Value |
|-----------|-------|
| **Source Port** | te2 (Device2) |
| **Destination Port** | te1 (Device1) |
| **Source IP** | 10.0.0.2 |
| **Destination IP** | 10.0.0.1 |
| **Source MAC** | 00:11:22:33:44:66 |
| **Dest MAC** | 00:11:22:33:44:55 |
| **Protocol** | UDP (src:5001, dst:5000) |
| **Packet Size** | 512 bytes (fixed) |
| **Rate** | 1000 pps |
| **Total Packets** | 120,000 (120 seconds @ 1000 pps) |
| **Expected Frames RX** | 120,000 (after BGP convergence) |

---

## Expected Behavior

### Protocol Startup Phase (0-30s)

1. **BGP session establishment:**
   - Device1 initiates BGP to Device2 (10.0.0.2)
   - Device2 initiates BGP to Device1 (10.0.0.1)
   - Expected convergence: **30 seconds** (industry standard)

2. **BGP route advertisement:**
   - Device1 advertises routes via AS 65001
   - Device2 advertises routes via AS 65002
   - Devices learn each other's routes

3. **BGP state transitions:**
   ```
   Idle → Connect → Active → OpenSent → OpenConfirm → Established
   ```

### Traffic Phase (30-120s)

1. **Flow 1 (te1 → te2):**
   - Transmit: 90,000 packets (30s × 1000 pps)
   - Expected RX: 90,000 packets (zero loss)

2. **Flow 2 (te2 → te1):**
   - Transmit: 90,000 packets (30s × 1000 pps)
   - Expected RX: 90,000 packets (zero loss)

3. **Total test time:** 120 seconds
4. **Total packets:** 240,000 (both flows combined)

---

## Port Alignment

**From ixia-c-deployment-agent:**
```
Deployment port mapping → OTG config location alignment:
├─ veth-a (TE-A, port 5555, protocol 50071) → te1
└─ veth-z (TE-Z, port 5555, protocol 50071) → te2
```

✅ **Alignment verified:** Port locations match infrastructure

---

## Validation Checklist

✅ **Schema Compliance**
- All required fields present
- Types correct (string, integer, array, object)
- References resolve (ports exist, devices valid, flows reference ports)

✅ **Port Configuration**
- 2 ports defined with correct locations
- Locations match deployment (veth-a, veth-z)
- No port name conflicts

✅ **Device Configuration**
- 2 devices, 1 per port
- BGP enabled on both devices
- IPv4 addressing correct (10.0.0.1/24, 10.0.0.2/24)
- BGP neighbors properly configured (AS 65001 ↔ AS 65002)

✅ **Traffic Flows**
- 2 flows (bidirectional)
- Packet headers complete (Ethernet, IPv4, UDP)
- MAC addresses match device configurations
- Rate: 1000 pps (achievable on 10GE)
- Duration: 120 seconds total

✅ **BGP Peering**
- eBGP enabled (different AS numbers)
- Neighbor addressing correct (10.0.0.1 ↔ 10.0.0.2)
- IPv4 unicast enabled on both devices

---

## Assertions (For snappi-script-generator)

The test should validate:

### 1. BGP Convergence ✓
**Condition:** BGP neighbors reach **Established** state within 30 seconds
```python
# Snappi equivalent:
# - Poll bgp_state() every 1 second for 30 seconds
# - Expect: state == "Established"
# - Assertion: time_to_convergence <= 30 seconds
```

### 2. Zero Packet Loss ✓
**Condition:** RX frames == TX frames on both flows (after BGP convergence)
```python
# Snappi equivalent:
# - Measure port stats after 120 seconds
# - Flow 1: rx_frames == 90,000 (expected after 30s BGP delay)
# - Flow 2: rx_frames == 90,000 (expected after 30s BGP delay)
# - Assertion: frame_loss == 0 on both flows
```

---

## JSON Structure

```
config/
├── ports (2 items)
│   ├── te1 (veth-a)
│   └── te2 (veth-z)
├── devices (2 items)
│   ├── device1 (AS 65001, 10.0.0.1/24)
│   │   ├── eth1 → te1
│   │   └── bgp (peers with 10.0.0.2)
│   └── device2 (AS 65002, 10.0.0.2/24)
│       ├── eth1 → te2
│       └── bgp (peers with 10.0.0.1)
└── flows (2 items)
    ├── flow_te1_to_te2 (1000 pps, 512B, 120k packets)
    └── flow_te2_to_te1 (1000 pps, 512B, 120k packets)
```

---

## Integration with snappi-script-generator

**Next step:** Pass this config to `@snappi-script-generator-agent`

**Required inputs for script generation:**
1. **OTG Config:** `bgp_convergence_cpdp.json` (this file) ✅
2. **Infrastructure YAML:**
   ```yaml
   controller:
     url: https://localhost:8443
     port: 8443
   ports:
     te1:
       location: veth-a
       container_ip: <from docker inspect>
     te2:
       location: veth-z
       container_ip: <from docker inspect>
   ```

---

## Example Snappi Script Output (Expected)

The generated script will:
1. **Connect** to controller at https://localhost:8443
2. **Push** this OTG config
3. **Start** protocol engines (BGP peers)
4. **Poll** BGP state until Established (max 30s)
5. **Start** traffic flows
6. **Wait** 120 seconds
7. **Collect** metrics (port stats, flow stats)
8. **Assert:**
   - BGP state == Established
   - Zero packet loss on both flows
9. **Stop** traffic
10. **Generate** JSON report with results

---

## File Reference

- **bgp_convergence_cpdp.json** — OTG configuration (JSON)
- **OTG_CONFIG_SUMMARY.md** — This file (reference)
- **docker-compose-bgp-cpdp.yml** — Infrastructure (from ixia-c-deployment-agent)
- **setup-ixia-c-bgp.sh** — Deployment script (from ixia-c-deployment-agent)

---

## Configuration Metadata

| Field | Value |
|-------|-------|
| **Ports** | 2 (te1, te2) |
| **Devices** | 2 (device1 AS 65001, device2 AS 65002) |
| **BGP Sessions** | 2 (1 per device) |
| **Flows** | 2 (bidirectional) |
| **Total Packets/Flow** | 120,000 |
| **Total Packets (both)** | 240,000 |
| **Packet Size** | 512 bytes |
| **Rate** | 1000 pps per flow |
| **Duration** | 120 seconds |
| **BGP Convergence Target** | 30 seconds |
| **Protocol Mode** | eBGP (different AS numbers) |
| **Transport** | IPv4 + UDP |

---

## Next Steps

1. **Deploy infrastructure** (if not already done):
   ```bash
   ./setup-ixia-c-bgp.sh
   ```

2. **Generate Snappi script:**
   ```bash
   @snappi-script-generator-agent
   Generate script from bgp_convergence_cpdp.json
   Controller: https://localhost:8443
   ```

3. **Run test:**
   ```bash
   python test_bgp_convergence.py
   ```

4. **Expected output:**
   ```
   ✅ BGP Established (converged in ~20-30 seconds)
   ✅ Flow 1: TX=90000, RX=90000 (zero loss)
   ✅ Flow 2: TX=90000, RX=90000 (zero loss)
   ✅ Test PASSED
   ```

---

**Configuration Complete!** ✅ Ready for script generation.
