# Invoking Subagents

This guide shows you what subagents are available and how to invoke them in Claude Code.

---

## Available Subagents

You have **4 subagents** defined in `.claude/agents/`:

### 🔵 **ixia-c-deployment-agent**
**Purpose:** Infrastructure provisioning and validation
**Invoke:** `@ixia-c-deployment-agent`

**Responsibilities:**
- Deploy Ixia-c (Docker Compose or Containerlab)
- Generate `docker-compose.yml` or `topo.clab.yml`
- Verify controller health and port discoverability
- Return port mapping for downstream agents

**When to use:**
- "Deploy Ixia-c for BGP testing with Docker Compose"
- "Set up Ixia-c with Containerlab for LAG testing"
- Need infrastructure before running tests

**Output:** Port mapping `{"te1": "location_1:5555", "te2": "location_2:5556"}`

---

### 🟢 **otg-config-generator-agent**
**Purpose:** Convert natural language intent → OTG JSON configuration
**Invoke:** `@otg-config-generator-agent`

**Responsibilities:**
- Parse test scenarios in natural language
- Generate valid OTG JSON config
- Inject port locations from deployment agent
- Validate schema compliance and alignment

**When to use:**
- "Create a BGP test with 2 ports, AS 65001/65002, bidirectional 1000 pps"
- Need to convert test intent into structured config
- Port mapping provided from deployment agent

**Output:** `otg_config.json` with ports, devices, flows, assertions

---

### 🟣 **snappi-script-generator-agent**
**Purpose:** Convert OTG config → standalone executable Python Snappi script
**Invoke:** `@snappi-script-generator-agent`

**Responsibilities:**
- Generate production-ready Python script from OTG config
- Embed all infrastructure details (controller URL, ports)
- Implement protocol setup, traffic control, metrics collection
- Add error handling and graceful cleanup

**When to use:**
- "Generate a Snappi script from bgp_config.json"
- Need executable test script (ready to run: `python test_*.py`)
- Have OTG config + infrastructure details

**Output:** `test_xxx.py` (standalone, executable, no external deps except Snappi)

---

### 🟠 **keng-licensing-agent**
**Purpose:** Licensing recommendations and cost estimation
**Invoke:** `@keng-licensing-agent`

**Responsibilities:**
- Calculate data plane costs (KENG-DPLU) based on port speeds
- Calculate control plane costs (KENG-CPLU) based on protocol sessions
- Recommend appropriate license tier (Developer/Team/System)
- Provide cost breakdown and tier comparison
- Include SE disclaimer

**When to use:**
- "What license do I need for 2×100GE + 4 BGP sessions?"
- "Compare Developer vs Team tier costs"
- Planning tests and need licensing guidance
- Can run in parallel with other agents

**Output:** License recommendation + cost estimate + tier comparison

---

## How to Invoke Subagents

### Direct Invocation in Claude Code

```bash
@ixia-c-deployment-agent Deploy Ixia-c for BGP testing with Docker Compose

@otg-config-generator-agent Create a BGP convergence test with 2 ports, AS 65001 and AS 65002, bidirectional traffic at 1000 pps

@snappi-script-generator-agent Generate a Snappi script from bgp_config.json, controller at localhost:8443

@keng-licensing-agent What license do I need for 4×100GE + 8 BGP sessions?
```

### Sequential Pipeline Example

```bash
# Step 1: Deploy infrastructure
@ixia-c-deployment-agent Deploy Ixia-c for BGP testing with Docker Compose

# Step 2: Generate OTG config (with port mapping from step 1)
@otg-config-generator-agent Create BGP test: 2 ports, AS 65001/65002, 1000 pps bidirectional

# Step 3: Generate executable script (with config from step 2 + infra from step 1)
@snappi-script-generator-agent Generate Snappi script from otg_config.json, controller at localhost:8443
```

### Parallel Execution Example

```bash
# Run licensing check in parallel with infrastructure setup
@keng-licensing-agent What license for 2×100GE + 4 BGP sessions?

@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose
# (both run independently, results come together)
```

---

## Agent Specifications & Eval Sets

### View Agent Specs
```bash
# High-level agent responsibilities and workflows
cat .claude/agents/README.md

# Detailed specification for each agent
cat .claude/agents/ixia-c-deployment-agent.md
cat .claude/agents/otg-config-generator-agent.md
cat .claude/agents/snappi-script-generator-agent.md
cat .claude/agents/keng-licensing-agent.md
```

### View Evaluation Sets (Test Cases)
```bash
# Overview of eval sets
cat .claude/agents/eval-sets/README.md

# 5 test questions per agent
cat .claude/agents/eval-sets/ixia-c-deployment-agent-eval.json
cat .claude/agents/eval-sets/otg-config-generator-agent-eval.json
cat .claude/agents/eval-sets/snappi-script-generator-agent-eval.json
cat .claude/agents/eval-sets/keng-licensing-agent-eval.json
```

---

## Quick Reference: When to Use Which Agent

| User Says | Agents to Invoke |
|-----------|-----------------|
| "Deploy Ixia-c for BGP" | 🔵 ixia-c-deployment only |
| "Create BGP test with 2 ports" | 🟢 otg-config-generator only |
| "Generate Snappi script from config" | 🟣 snappi-script-generator only |
| "What license for 4×100GE?" | 🟠 keng-licensing only |
| "Deploy + create + script" | 🔵 → 🟢 → 🟣 (sequential) |
| "Deploy + script + check licensing" | 🔵 → 🟢 → 🟣 + 🟠 (parallel licensing) |
| "I have Ixia-c; create test + script" | 🟢 → 🟣 (skip deployment) |

---

## Examples by Use Case

### Use Case 1: Full Greenfield Test
**User:** "Create a BGP convergence test with 2 ports, AS 65001 and 65002, deploy with Docker, give me a runnable script, and tell me the license cost."

**Subagents to invoke:**
```
🔵 ixia-c-deployment-agent
   → Deploy Ixia-c with Docker Compose for 2 ports
   → Output: docker-compose.yml, port_mapping

🟠 keng-licensing-agent (parallel)
   → Calculate cost for 2 ports + BGP sessions
   → Output: License recommendation + cost

🟢 otg-config-generator-agent (wait for port_mapping)
   → Create BGP config with port locations injected
   → Output: otg_config.json

🟣 snappi-script-generator-agent (wait for config)
   → Generate Snappi script
   → Output: test_bgp_convergence.py
```

---

### Use Case 2: Existing Infrastructure
**User:** "I have Ixia-c running at localhost:8443. Create a BGP test and give me the script."

**Subagents to invoke:**
```
🟢 otg-config-generator-agent
   → Create BGP config
   → Output: otg_config.json

🟣 snappi-script-generator-agent (wait for config)
   → Generate Snappi script with controller at localhost:8443
   → Output: test_bgp.py
```

---

### Use Case 3: Quick Licensing Check
**User:** "What license do I need for 4×100GE ports and 8 BGP sessions?"

**Subagents to invoke:**
```
🟠 keng-licensing-agent
   → Calculate costs
   → Output: License tier + cost breakdown + SE disclaimer
```

---

### Use Case 4: Infrastructure Only
**User:** "Just deploy Ixia-c with Containerlab for LAG testing."

**Subagents to invoke:**
```
🔵 ixia-c-deployment-agent
   → Deploy with Containerlab
   → Output: topo.clab.yml, port_mapping, verification commands
```

---

## Agent Colors (Unique)

```
🔵 Blue       → ixia-c-deployment-agent
🟢 Green      → otg-config-generator-agent
🟣 Purple     → snappi-script-generator-agent
🟠 Orange     → keng-licensing-agent
```

---

## Status

All subagents are **production-ready** ✅ and can be invoked independently or chained together in workflows!

For more details, see:
- **CLAUDE.md** — Development guidance
- **.claude/agents/README.md** — Agent specifications and workflows
- **.claude/agents/eval-sets/README.md** — Evaluation framework and test cases
- **AGENT_ORCHESTRATION_PLAN.md** — Detailed orchestration patterns
