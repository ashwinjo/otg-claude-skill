---
name: kengotg-eval-agents
description: Agent evaluation framework and test cases
disable-model-invocation: false
allowed-tools: []
---

# Eval-Agents — Evaluation Framework

Overview of the 20 evaluation questions used to validate agent quality and capabilities.

---

## Evaluation Framework Overview

Each of the 4 agents is evaluated with **5 test questions** covering:

- **Happy Path:** Standard, well-defined scenarios
- **Edge Cases:** Infrastructure constraints, conflicts
- **Complexity:** Multi-protocol, advanced features
- **Error Handling:** Graceful failure, clear messages
- **Real-World:** Production scenarios

**Total:** 20 evaluation questions (5 per agent)

Each question includes:
- **Scenario:** Test description
- **Inputs:** What the agent receives
- **Expected Output:** What success looks like
- **Success Criteria:** Pass/fail metrics

---

## 🔵 ixia-c-deployment-agent Evaluations

### Evaluation 1: Simple Docker Compose Deployment
**Scenario:** Deploy Ixia-c for a basic BGP test

**Input:**
- Topology: Docker Compose
- Protocol: BGP
- Port count: 2

**Expected Output:**
- `docker-compose-bgp-cpdp.yml` generated
- 5 services defined (controller, 2×TE, 2×PE)
- Port mapping returned
- Health check commands provided

**Success Criteria:**
- ✓ docker-compose.yml is valid YAML
- ✓ All required services present
- ✓ Port mapping includes all locations
- ✓ Controller URL correct (localhost:8443)

### Evaluation 2: Containerlab Multi-Protocol Deployment
**Scenario:** Deploy Ixia-c with Containerlab for complex topology

**Input:**
- Topology: Containerlab
- Protocols: BGP + OSPF + LACP
- Port count: 8
- Multi-host setup

**Expected Output:**
- `topo.clab.yml` generated with network topology
- Container definitions for TE, PE, auxiliary nodes
- Port mapping for all 8 locations
- Network linking configuration

**Success Criteria:**
- ✓ topo.clab.yml is valid YAML
- ✓ All containers defined
- ✓ Network links configured correctly
- ✓ Port mapping complete and consistent

### Evaluation 3: Port Mapping & Alignment
**Scenario:** Return correct port locations for downstream agents

**Input:**
- 4 ports requested
- Docker Compose deployment
- Veth pair naming convention

**Expected Output:**
- Port mapping in standardized format
- Clear location names (e.g., veth-a, veth-b, veth-c, veth-d)
- Controller details (URL, port)
- No null or ambiguous values

**Success Criteria:**
- ✓ Port count matches request
- ✓ Locations are unambiguous
- ✓ Format is JSON (parseable by next agent)
- ✓ No missing required fields

### Evaluation 4: Health Check & Validation
**Scenario:** Verify deployment health after setup

**Input:**
- Deployed infrastructure
- Request: Verify controller + ports ready

**Expected Output:**
- Controller reachability confirmed
- All traffic engines responsive
- Port connectivity validated
- Health check commands provided

**Success Criteria:**
- ✓ Controller responds to HTTP/HTTPS
- ✓ All TEs discoverable
- ✓ Verification steps are clear
- ✓ Troubleshooting guidance included

### Evaluation 5: Deployment Failure Recovery
**Scenario:** Handle deployment errors gracefully

**Input:**
- Insufficient disk space (Docker)
- Network name conflict (Containerlab)
- Port already in use
- Docker daemon not running

**Expected Output:**
- Clear error message identifying the problem
- Suggested corrective action
- Rollback instructions
- Prevention strategy for future

**Success Criteria:**
- ✓ Error message is not generic
- ✓ Root cause identified
- ✓ Solution is actionable
- ✓ Fallback options provided

---

## 🟢 otg-config-generator-agent Evaluations

### Evaluation 1: Basic BGP Configuration
**Scenario:** Convert simple BGP test intent to OTG config

**Input:**
- "Create BGP test: 2 ports, AS 65001 and AS 65002, bidirectional 1000 pps"
- Port mapping: `{"te1": "veth-a", "te2": "veth-z"}`

**Expected Output:**
- Valid OTG JSON config
- 2 ports defined with correct locations
- 2 BGP devices with correct AS numbers
- 2 bidirectional traffic flows
- Assertions for BGP state and packet loss

**Success Criteria:**
- ✓ OTG validates against openapi.yaml
- ✓ Ports align with provided mapping
- ✓ BGP configuration is complete
- ✓ Traffic flows are bidirectional
- ✓ Assertions are present and meaningful

### Evaluation 2: Multi-Protocol Complex Setup
**Scenario:** Generate config for BGP + OSPF + LACP interaction

**Input:**
- "Create test: BGP on LAG1, OSPF on LAG2, simulate LAG failover"
- 4 ports, request priority-based traffic routing
- Port mapping provided

**Expected Output:**
- OTG config with LAGs defined
- BGP devices on LAG1 (AS 65001 vs 65002)
- OSPF devices on LAG2 (Area 0 vs Area 1)
- Traffic flows respecting LAG membership
- Assertions for all protocols + LAG state

**Success Criteria:**
- ✓ All protocols properly configured
- ✓ LAGs defined correctly
- ✓ Devices assigned to correct LAGs
- ✓ No protocol conflicts
- ✓ Failover scenario clear in config

### Evaluation 3: Port Alignment Validation
**Scenario:** Ensure config ports align with infrastructure

**Input:**
- Port mapping: `{"te1": "veth-a", "te2": "veth-z", "te3": "veth-b", "te4": "veth-c"}`
- Intent: "4 port test with 2 LAGs"
- Requirement: All ports must be used

**Expected Output:**
- OTG config uses all 4 ports
- Port names match provided locations exactly
- No ambiguous or null location references
- Alignment report showing mapping

**Success Criteria:**
- ✓ All 4 ports in config
- ✓ Port locations match infrastructure
- ✓ No unused ports
- ✓ Locations are verified/validated

### Evaluation 4: Ambiguous Intent Handling
**Scenario:** Handle incomplete or vague user intent

**Input:**
- "Create a test" (no protocol specified)
- "Configure BGP" (no port count, AS numbers)
- "Measure traffic" (no packet size, duration)

**Expected Output:**
- Clear list of clarifying questions
- Suggested defaults
- Example of well-defined intent
- Not a silent failure with bad assumptions

**Success Criteria:**
- ✓ Agent asks for missing information
- ✓ Suggestions are reasonable
- ✓ No assumption-based config generation
- ✓ User guided to proper input

### Evaluation 5: Assertion Feasibility Check
**Scenario:** Validate that requested assertions are achievable

**Input:**
- Assertion: "BGP converges in < 1 second" (unrealistic)
- Assertion: "Zero packet loss on 100GE at 100% load" (infeasible)
- Assertion: "BGP state UP within 30 seconds" (reasonable)

**Expected Output:**
- Feasibility assessment for each assertion
- Warnings for unrealistic expectations
- Suggestions for achievable alternatives
- Rationale for recommendations

**Success Criteria:**
- ✓ Unrealistic assertions flagged
- ✓ Rationale provided (e.g., protocol convergence times)
- ✓ Alternative suggestions are practical
- ✓ Config includes only feasible assertions

---

## 🟣 snappi-script-generator-agent Evaluations

### Evaluation 1: Standalone Script Generation
**Scenario:** Generate Python script that requires no external files

**Input:**
- otg_config.json (BGP test config)
- Controller URL: localhost:8443
- Request: Executable script

**Expected Output:**
- `test_bgp_convergence.py` (649+ lines)
- Entire OTG config embedded in Python
- All imports satisfied (Snappi SDK only)
- Executable: `python test_bgp_convergence.py`

**Success Criteria:**
- ✓ Script runs without external config files
- ✓ No missing imports
- ✓ OTG config fully embedded
- ✓ No file I/O for config (only for reports)
- ✓ Script validates immediately with `python -m py_compile`

### Evaluation 2: Connection Error Handling
**Scenario:** Script handles controller connection failures gracefully

**Input:**
- Controller URL: localhost:8443 (assume offline)
- OTG config requiring connectivity

**Expected Output:**
- Script attempts connection (with retries)
- Clear error message on failure (not generic)
- Actionable troubleshooting steps
- Graceful exit without hanging

**Success Criteria:**
- ✓ Retry logic implemented (exponential backoff)
- ✓ Timeout is reasonable (not infinite wait)
- ✓ Error message identifies controller URL issue
- ✓ Exit code non-zero on failure
- ✓ No hanging processes

### Evaluation 3: BGP State Polling & Convergence
**Scenario:** Script polls BGP state and measures convergence time

**Input:**
- OTG config with BGP devices
- Duration: 120 seconds
- Assertion: BGP converges within 30 seconds

**Expected Output:**
- Script polls BGP adjacency state at intervals
- Measures time from config applied to convergence
- Reports convergence time or timeout
- Assertion pass/fail in final report

**Success Criteria:**
- ✓ BGP state polling implemented
- ✓ Convergence time measured accurately
- ✓ Timeout handling (30s default)
- ✓ Results in JSON report
- ✓ Assertion evaluated correctly

### Evaluation 4: Metrics Collection & Assertions
**Scenario:** Script collects metrics and validates assertions

**Input:**
- OTG config with traffic flows
- Assertions: throughput > 1000 pps, loss = 0%
- Metrics requested: pps, packet loss, latency

**Expected Output:**
- Script collects all requested metrics
- Calculates assertion conditions
- Reports pass/fail for each
- JSON report includes metric values + assertions

**Success Criteria:**
- ✓ Metrics collection implemented
- ✓ All requested metrics present in report
- ✓ Assertions evaluated against metrics
- ✓ Assertion logic correct (>, <, ==, ranges)
- ✓ Report clearly shows pass/fail

### Evaluation 5: Cleanup & Error Recovery
**Scenario:** Script cleans up resources on completion or error

**Input:**
- Script execution with potential errors
- Request: Cleanup, stop traffic, close connections
- Scenario: Ctrl+C during test, connection loss

**Expected Output:**
- Traffic stopped cleanly
- Connections closed
- JSON report saved even on error
- No hanging resources
- Clear final status

**Success Criteria:**
- ✓ Try/finally blocks for cleanup
- ✓ Traffic stopped before exit
- ✓ Connections explicitly closed
- ✓ Report generated even on partial failure
- ✓ No resource leaks (verified with `lsof`, `ps`)

---

## 🟠 keng-licensing-agent Evaluations

### Evaluation 1: POC Licensing Recommendation
**Scenario:** Recommend license for proof-of-concept deployment

**Input:**
- 2×100GE ports
- 4 BGP sessions
- Use case: POC / evaluation

**Expected Output:**
- DPLU cost: 2×100 = 200 DPLU
- CPLU cost: 4×1 = 4 CPLU
- Recommendation: Developer tier (250 DPLU, 10 CPLU)
- Cost estimate + comparison

**Success Criteria:**
- ✓ DPLU calculation correct (200)
- ✓ CPLU calculation correct (4)
- ✓ Tier recommendation justified
- ✓ Cost breakdown provided
- ✓ SE disclaimer included

### Evaluation 2: Tier Comparison
**Scenario:** Compare licensing costs across tier options

**Input:**
- 4×100GE + 8 BGP sessions
- Request: Which tier is best value?

**Expected Output:**
```
Developer: Not enough capacity (max 250 DPLU, 10 CPLU)
Team: 1000 DPLU, 50 CPLU → Sufficient → Cost: $Y/month
System: Unlimited → Overkill → Cost: $Z/month
Recommendation: Team tier
```

**Success Criteria:**
- ✓ All tiers evaluated for capacity
- ✓ Infeasible tiers identified
- ✓ Cost comparison shown
- ✓ Recommendation with rationale
- ✓ SE disclaimer included

### Evaluation 3: High Session Count Calculation
**Scenario:** Calculate costs for complex multi-protocol setup

**Input:**
- 4×100GE ports (400 DPLU)
- 20 BGP sessions (20 CPLU)
- 10 OSPF sessions (10 CPLU)
- 5 LAGs (2.5 CPLU)
- Total CPLU: 32.5

**Expected Output:**
- Correct DPLU total: 400
- Correct CPLU total: 32.5
- Recommended tier: Team or System
- Cost estimate

**Success Criteria:**
- ✓ DPLU math correct (400)
- ✓ CPLU math correct (32.5, including LAGs)
- ✓ Tier recommendation justified (Team if available, else System)
- ✓ Alternative options if exact fit unavailable

### Evaluation 4: Cost Optimization Suggestion
**Scenario:** Provide cost optimization recommendations

**Input:**
- User wants 10×25GE (250 DPLU)
- Currently considering: 4×100GE (400 DPLU)
- Use case: Not all ports needed immediately

**Expected Output:**
- Alternative 1: Start with 4×25GE (100 DPLU), upgrade later
- Alternative 2: Start with 2×100GE (200 DPLU), less expensive
- Cost savings calculations
- Expandability considerations

**Success Criteria:**
- ✓ Multiple options presented
- ✓ Cost savings calculated
- ✓ Trade-offs explained (capacity vs. cost)
- ✓ Upgrade path clear
- ✓ SE disclaimer on recommendations

### Evaluation 5: Disclaimer Accuracy
**Scenario:** Ensure licensing disclaimers are complete and accurate

**Input:**
- Cost estimate request
- Any licensing recommendation

**Expected Output:**
- Clear disclaimer: "Costs are estimates; verify with SE"
- Clarification on regional pricing variations
- Note on complex features (may increase cost)
- Reference to official pricing

**Success Criteria:**
- ✓ SE disclaimer present and clear
- ✓ Estimates marked as "approximate"
- ✓ No false guarantees or promises
- ✓ Guidance to official sources
- ✓ Compliance with Keysight/licensing policies

---

## Evaluation Framework Metrics

### Scoring System
```
✓ Pass: Agent meets all success criteria
◐ Partial: Agent meets 70%+ of criteria, minor issues
✗ Fail: Agent misses key criteria or produces errors
```

### Quality Metrics
```
Correctness:      Does output match expected result?
Completeness:     Are all required fields/elements present?
Clarity:          Is output clear and well-formatted?
Robustness:       Handles edge cases and errors?
Alignment:        Matches architectural patterns?
```

### Agent Scoring
```
5/5 questions pass      = Production-Ready ✓
4/5 questions pass      = Ready with caveats ◐
<4/5 questions pass     = Needs revision ✗
```

---

## Running Evaluations

### Manual Evaluation
```bash
1. Read evaluation scenario
2. Invoke agent with test input
3. Review output against success criteria
4. Document pass/fail + notes
```

### Example
```
Scenario: Simple Docker Compose Deployment
Command:  @ixia-c-deployment-agent Deploy Ixia-c with Docker Compose
Output:   [review docker-compose.yml against criteria]
Result:   ✓ Pass (all 4 criteria met)
```

---

## Evaluation Files

Access detailed evaluation questions:

```bash
# Agent evaluation sets (5 questions per agent)
cat .claude/agents/eval-sets/ixia-c-deployment-agent-eval.json
cat .claude/agents/eval-sets/otg-config-generator-agent-eval.json
cat .claude/agents/eval-sets/snappi-script-generator-agent-eval.json
cat .claude/agents/eval-sets/keng-licensing-agent-eval.json

# Skill evaluation sets (3-5 questions per skill)
cat .claude/skills/*/evals/evals.json
```

---

## See Also

- `/kengotg-show-agents` — Agent responsibilities
- `/kengotg-show-architecture` — Orchestration patterns
- `/kengotg-examples` — Real-world test scenarios
- `/kengotg-skill-help` — Detailed skill documentation
- `.claude/agents/eval-sets/README.md` — Evaluation framework guide
