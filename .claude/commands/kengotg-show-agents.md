---
name: kengotg-show-agents
description: List all 5 intelligent subagents and their responsibilities
disable-model-invocation: false
allowed-tools: []
---

# Show Agents

Display all 5 intelligent subagents orchestrated by the KENG OTG Pipeline.

## Command → Agent → Skill Hierarchy

All Section A slash commands dispatch to agents (never invoke skills directly):

```
/kengotg-deploy-ixia    → ixia-c-deployment-agent          → ixia-c-deployment skill
/kengotg-otg-gen        → otg-config-generator-agent       → otg-config-generator skill
/kengotg-snappi-script  → snappi-script-generator-agent    → snappi-script-generator skill
/kengotg-licensing      → keng-licensing-agent              → keng-licensing skill
/kengotg-migrate-ix     → ixnetwork-to-keng-converter-agent → ixnetwork-to-keng-converter skill
```

---

## Available Agents

### 🔵 **ixia-c-deployment-agent**
**Role:** Infrastructure provisioner and deployer

**Responsibilities:**
- Analyze deployment requirements (Docker Compose vs Containerlab)
- Generate infrastructure manifests (docker-compose.yml, topo.clab.yml)
- Configure veth pairs, network namespaces, and controller locations
- Validate controller health and port connectivity
- Return port mapping for downstream agents

**Invoke:**
```
@ixia-c-deployment-agent Deploy Ixia-c for BGP testing with Docker Compose
```

**Success Criteria:**
- Controller reachable and healthy
- All ports discoverable
- Port mapping returned in standardized format

**Related Skill:** `/ixia-c-deployment`

---

### 🟢 **otg-config-generator-agent**
**Role:** Intent translator (natural language → OTG config)

**Responsibilities:**
- Parse test scenario descriptions
- Validate protocol and feature support
- Inject port locations from deployment agent
- Generate standards-compliant OTG JSON config
- Align port names with infrastructure locations
- Validate against OTG schema

**Invoke:**
```
@otg-config-generator-agent Create BGP test: 2 ports, AS 65001/65002, 1000 pps bidirectional
```

**Success Criteria:**
- OTG config validates against schema
- All ports align with infrastructure
- Device/flow/assertion definitions are complete
- Config is production-ready

**Related Skill:** `/otg-config-generator`

---

### 🟣 **snappi-script-generator-agent**
**Role:** Script executor (OTG config → executable Python)

**Responsibilities:**
- Generate standalone Python Snappi scripts
- Embed OTG config and infrastructure details
- Implement protocol setup, traffic control, state polling
- Add assertions, metrics collection, error handling
- Generate cleanup and JSON reporting logic
- Validate script syntax and Snappi imports
- Ensure scripts are immediately executable

**Invoke:**
```
@snappi-script-generator-agent Generate Snappi test script from bgp_convergence.json
```

**Success Criteria:**
- Script executes without external config files
- Error handling covers connection, timeout, protocol failures
- Metrics and assertions properly integrated
- JSON report generated with clear results

**Related Skill:** `/snappi-script-generator`

---

### 🟠 **keng-licensing-agent**
**Role:** Licensing advisor and cost estimator

**Responsibilities:**
- Calculate data plane costs (KENG-DPLU) based on port speeds
- Calculate control plane costs (KENG-CPLU) based on session count
- Recommend license tier (Developer/Team/System)
- Provide cost breakdown and tier comparison
- Include Solutions Engineer disclaimers
- Validate licensing assumptions

**Invoke:**
```
@keng-licensing-agent What license do I need for 4×100GE + 8 BGP sessions?
```

**Success Criteria:**
- Cost calculations are accurate (DPLU/CPLU formulas)
- Recommendations match user requirements
- Tier comparison is complete
- SE disclaimer included

**Related Skill:** `/keng-licensing`

---

### 🔴 **ixnetwork-to-keng-converter-agent**
**Role:** IxNetwork migration specialist

**Responsibilities:**
- Detect input format (RestPy Python code or IxNetwork JSON)
- Run feasibility analysis (% convertible, blockers vs workarounds)
- Convert supported features to OTG-compliant JSON config
- Generate detailed conversion report
- Suggest workarounds for unsupported features
- Recommend next steps (enhance with otg-config-generator, generate script)

**Invoke:**
```
@ixnetwork-to-keng-converter-agent Convert this IxNetwork BGP config to OTG format
```

**Success Criteria:**
- Feasibility score accurately reflects convertibility
- Supported features correctly mapped to OTG schema
- Unsupported features clearly listed with severity
- Conversion report is actionable

**Related Skill:** `/ixnetwork-to-keng-converter`
**Slash Command:** `/kengotg-migrate-ix`

---

## Orchestration Patterns

### Sequential (Greenfield Test)
```
ixia-c-deployment-agent
  ↓ (returns port_mapping)
otg-config-generator-agent
  ↓ (returns otg_config.json)
snappi-script-generator-agent
  ↓ (returns test_xxx.py)
```

### Parallel (Deploy + License Check)
```
ixia-c-deployment-agent  ┐
                          ├→ Both run independently
keng-licensing-agent      ┘
  ↓
otg-config-generator-agent
  ↓
snappi-script-generator-agent
```

### Existing Infrastructure (Skip Deployment)
```
otg-config-generator-agent
  ↓
snappi-script-generator-agent
```

### Licensing Only
```
keng-licensing-agent (standalone)
```

---

## Agent Evaluation Framework

Each agent has **5 evaluation questions** testing:
- Happy path (standard workflow)
- Infrastructure edge cases
- Protocol complexity
- Error handling
- Real-world scenarios

View evaluation questions:
```bash
cat .claude/agents/eval-sets/ixia-c-deployment-agent-eval.json
cat .claude/agents/eval-sets/otg-config-generator-agent-eval.json
cat .claude/agents/eval-sets/snappi-script-generator-agent-eval.json
cat .claude/agents/eval-sets/keng-licensing-agent-eval.json
```

Total: **20+ evaluation questions** (5 per agent, 5 agents)

---

## Decision Tree: Which Agent(s) to Invoke?

```
User says: "Deploy Ixia-c for BGP"
→ 🔵 ixia-c-deployment-agent only

User says: "Create a BGP test and deploy"
→ 🔵 → 🟢 → 🟣 (sequential)

User says: "I have Ixia-c at localhost:8443; create test"
→ 🟢 → 🟣 (skip deployment)

User says: "What license for 4×100GE + 8 BGP?"
→ 🟠 only

User says: "Full test setup + license cost"
→ 🔵 + 🟠 (parallel) → 🟢 → 🟣

User says: "Convert my IxNetwork config to OTG"
→ 🔴 only

User says: "Migrate IxNetwork config and run it"
→ 🔴 → 🟢 → 🟣 (sequential)
```

---

## Next Steps

1. **See agent specifications:**
   ```
   cat .claude/agents/README.md
   cat .claude/agents/ixia-c-deployment-agent.md
   ```

2. **View evaluation questions:**
   ```
   /eval-agents
   ```

3. **See workflow examples:**
   ```
   /examples
   ```

4. **View orchestration architecture:**
   ```
   /show-architecture
   ```
