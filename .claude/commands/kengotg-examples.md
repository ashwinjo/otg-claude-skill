---
name: kengotg-examples
description: Workflow examples by use case
disable-model-invocation: false
allowed-tools: []
---

# Workflow Examples

Real-world examples showing how to use the KENG OTG Pipeline for different scenarios.

---

## Example 1: Complete Greenfield BGP Test

**Scenario:** Build a BGP convergence test from scratch with infrastructure deployment.

### Step 1: Deploy Infrastructure
```
@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose for BGP testing with 2 traffic engines
```

**Agent decides:**
- Docker Compose (simpler, single host)
- 2 traffic engines (TE-A, TE-Z)
- Veth pair (veth-a ↔ veth-z)
- Controller on localhost:8443

**Outputs:**
- `docker-compose-bgp-cpdp.yml` (5 services: controller, TE-A, TE-Z, PE-A, PE-Z)
- `setup-ixia-c-bgp.sh` (deployment automation script)
- Port mapping: `{"te1": "veth-a", "te2": "veth-z"}`

### Step 2: Generate OTG Configuration
```
@otg-config-generator-agent Create BGP convergence test with 2 ports (te1, te2), AS 65001 and AS 65002,
bidirectional traffic 1000 pps, 120 second duration, measure BGP convergence time
```

**Agent:**
- Parses intent (BGP, 2 ports, 1000 pps, 120s)
- Injects port mapping from step 1 (te1→veth-a, te2→veth-z)
- Generates 2 BGP devices
- Creates bidirectional traffic flows
- Adds assertions (BGP state, packet loss)
- Validates OTG schema

**Output:** `bgp_convergence_cpdp.json` (OTG schema-compliant)

### Step 3: Generate Executable Script
```
@snappi-script-generator-agent Generate Snappi test script from bgp_convergence_cpdp.json with controller at localhost:8443
```

**Agent:**
- Embeds OTG config in Python
- Implements BGP state polling
- Adds traffic control (start/stop)
- Implements metrics collection
- Adds assertions and error handling
- Generates JSON report on completion
- Validates Python syntax

**Output:** `test_bgp_convergence.py` (649 lines, production-ready)

### Step 4: Execute Test
```
bash setup-ixia-c-bgp.sh    # Deploy infrastructure
python test_bgp_convergence.py  # Run test
```

**Results:**
- JSON report with BGP convergence metrics
- Traffic statistics
- Pass/fail assertions

---

## Example 2: Quick License Check

**Scenario:** Determine licensing cost before purchasing test infrastructure.

```
@keng-licensing-agent What license do I need for 4×100GE ports with 8 BGP sessions?
```

**Agent calculates:**
- DPLU cost: 4 ports × 100GE = 400 DPLU units
- CPLU cost: 8 BGP sessions = 8 CPLU units
- Recommends: Team tier (covers 500 DPLU, 20 CPLU)
- Provides cost breakdown
- Includes SE disclaimer

**Output:** License recommendation with cost estimate

---

## Example 3: IxNetwork to KENG Migration

**Scenario:** Migrate existing IxNetwork test to OTG format.

### Input: IxNetwork Config
```python
# IxNetwork RestPy code
ixnObj = IxNetwork()
ixnObj.connect(ixnIp, 443, 'admin', 'admin')
vport1 = ixnObj.Vport.add()
vport2 = ixnObj.Vport.add()
bgp1 = vport1.Protocols.Bgp.add()
bgp1.RouterId = '1.1.1.1'
bgp1.AsNumber = 65001
# ... more configuration
```

### Step 1: Check Feasibility & Convert
```
@ixnetwork-to-keng-converter [paste IxNetwork config]
```

**Agent:**
- Analyzes IxNetwork config
- Lists supported features ✓ and unsupported ✗
- Provides migration feasibility score
- Generates equivalent OTG config
- Creates conversion report

**Output:**
- Feasibility report (e.g., "85% convertible")
- OTG config JSON (for supported features)
- Conversion report (mapping table)

### Step 2: Generate Test Script
```
@snappi-script-generator-agent Generate test script from converted OTG config with controller at localhost:8443
```

**Output:** `test_migrated_bgp.py` (ready to run)

---

## Example 4: Existing Infrastructure + Custom Test

**Scenario:** Ixia-c already running; need to create a new LACP failover test.

### Step 1: Generate Config
```
@otg-config-generator-agent Create LACP failover test with 4 ports (port1-4),
2 LAG groups (LAG1: ports 1-2, LAG2: ports 3-4),
simulate failover from LAG1 to LAG2, measure convergence time
```

**Agent:**
- Parses LACP intent
- No deployment needed (you provide existing infrastructure)
- Uses your port locations (or asks for clarification)
- Generates OTG config with LAG setup

**Output:** `lacp_failover_cpdp.json`

### Step 2: Generate Script
```
@snappi-script-generator-agent Generate test script with controller at my-ixia-c.internal:8443
```

**Agent:**
- Embeds controller URL
- Implements port assignment
- Adds LAG state monitoring
- Implements failover simulation
- Measures convergence

**Output:** `test_lacp_failover.py`

### Step 3: Run
```
python test_lacp_failover.py
```

---

## Example 5: Multi-Protocol Complex Test

**Scenario:** BGP + OSPF + LACP on same topology.

```
@otg-config-generator-agent Create multi-protocol test:
- 4 ports (port1-4)
- 2 LAGs (LAG1: ports 1-2, LAG2: ports 3-4)
- BGP on LAG1 (AS 65001 vs 65002)
- OSPF on LAG2 (Area 0 and Area 1)
- 2 Mbps bidirectional traffic
- Measure BGP+OSPF convergence on LAG failover
- Assert: All protocols converge within 30 seconds
```

**Agent:**
- Validates multi-protocol support ✓
- Checks for feature conflicts ✓
- Generates unified OTG config
- Implements assertions for both protocols

**Output:** `multi_protocol_test.json`

```
@snappi-script-generator-agent Generate test script for multi-protocol test
```

**Output:** `test_multi_protocol.py` (handles protocol setup, failover simulation, metrics)

---

## Example 6: Licensing + Full Pipeline (Parallel Execution)

**Scenario:** Plan test infrastructure, get licensing cost, deploy, and create test.

### Run in Parallel:
```
@keng-licensing-agent What license for 2×100GE + 4 BGP + 2 OSPF sessions?

@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose for multi-protocol testing
```

Both agents run independently.

### Wait for Results, Then Sequential:
```
@otg-config-generator-agent Create multi-protocol test: BGP + OSPF on 2 ports (from deployment)

@snappi-script-generator-agent Generate test script
```

**Outputs:**
- License recommendation + cost
- Infrastructure deployment files
- OTG config
- Executable test script

---

## Example 7: Performance Baseline Test

**Scenario:** Measure traffic throughput across different packet sizes.

```
@otg-config-generator-agent Create throughput baseline test:
- 2 ports
- Variable packet sizes: 64, 256, 512, 1500 bytes
- Run 30 seconds per size
- Measure: throughput (pps), latency (min/max/avg)
- Assert: Throughput >= 1Mpps for all sizes
```

**Agent:**
- Generates 4 test flows (one per packet size)
- Adds throughput and latency assertions
- Implements sequential flow execution

**Output:** `baseline_throughput.json`

```
@snappi-script-generator-agent Generate performance baseline script
```

**Output:** `test_performance_baseline.py` (runs all sizes, generates comparison report)

---

## Example 8: Minimal Validation Test

**Scenario:** Quick connectivity check (ports up, MAC learning, basic traffic).

```
@otg-config-generator-agent Create simple port connectivity test:
- 2 ports
- 1 flow: 100 pps, 10 second duration
- Assert: Packets transmitted = packets received (no loss)
```

**Agent:**
- Minimal config (no protocols)
- Simple assertions
- Fast execution

**Output:** `connectivity_check.json` (small, fast)

```
@snappi-script-generator-agent Generate connectivity test script
```

**Output:** `test_connectivity.py` (50-100 lines, 10 second runtime)

---

## Quick Reference Table

| Scenario | Agents | Sequence | Approx. Time |
|----------|--------|----------|--------------|
| Greenfield (deploy+config+script) | 🔵→🟢→🟣 | Sequential | 2-3 min |
| License check | 🟠 | - | 1 min |
| IxNetwork migration | 🔵→🟢→🟣 | Sequential (or skip deploy) | 3-5 min |
| Existing infra (config+script) | 🟢→🟣 | Sequential | 1-2 min |
| Full pipeline (parallel licensing) | 🔵\|🟠→🟢→🟣 | Parallel + Seq | 2-3 min |
| Multi-protocol complex | 🟢→🟣 | Sequential | 2-3 min |
| Performance baseline | 🟢→🟣 | Sequential | 1-2 min |
| Minimal connectivity | 🟢→🟣 | Sequential | 1 min |

---

## Decision Tree: Which Example Matches My Scenario?

```
Do you have Ixia-c running?
├─ No  → Need deploy
│  ├─ With licensing check? → Example 6 (greenfield + license)
│  └─ Without? → Example 1 (greenfield basic)
│
├─ Yes → Skip deploy
│  ├─ Simple test? → Example 8 (connectivity)
│  ├─ BGP/OSPF test? → Example 4 (existing infra)
│  ├─ LACP test? → Example 4 (modified)
│  ├─ Multi-protocol? → Example 5
│  └─ Performance? → Example 7
│
Do you have IxNetwork config?
├─ Yes → Example 3 (migration)
└─ No  → Use examples above
```

---

## See Also

- `/kengotg-show-skills` — Skill descriptions
- `/kengotg-show-agents` — Agent details
- `/kengotg-show-architecture` — Workflow diagrams
- `/kengotg-eval-agents` — Evaluation framework
- `/kengotg-keng-help` — Plugin overview

For more examples and troubleshooting:
```bash
cat AGENT_ORCHESTRATION_PLAN.md
cat README.md
```
