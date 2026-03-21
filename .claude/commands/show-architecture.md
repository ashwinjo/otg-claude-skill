---
name: show-architecture
description: Display orchestration architecture and workflow diagrams
disable-model-invocation: false
allowed-tools: []
---

# Show Architecture

Visualize the KENG OTG Traffic Testing Pipeline architecture and orchestration patterns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLAUDE CODE                                │
│                       (Orchestrator)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    Classifies User Intent
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
   Greenfield            Existing Infra         Licensing Check
   (3 agents)            (2 agents)              (1 agent)
        │                        │                        │
        ▼                        ▼                        ▼
   🔵Deploy          🟢Config+         🟠Licensing
   🟢Config          🟣Script         (standalone)
   🟣Script
```

---

## Greenfield Test Pipeline (Most Common)

### 1️⃣ **Deployment Phase** (🔵 ixia-c-deployment-agent)

```
User Intent: "Deploy Ixia-c for BGP testing"
             │
             ▼
    ┌────────────────┐
    │ Agent analyzes │
    │ requirements   │
    └────────────────┘
             │
             ├─ Docker Compose? (simple, 1 host)
             │  └─ Generate docker-compose.yml
             │
             └─ Containerlab? (complex, multi-host)
                └─ Generate topo.clab.yml

             ▼
    ┌─────────────────────────┐
    │ Deploy to Docker/Clab   │
    │ Configure controller    │
    │ Create veth pairs       │
    │ Inject port locations   │
    └─────────────────────────┘
             │
             ▼
    📤 OUTPUT: Port Mapping
       {
         "te1": "veth-a",
         "te2": "veth-z",
         "controller": "https://localhost:8443"
       }
```

### 2️⃣ **Configuration Phase** (🟢 otg-config-generator-agent)

```
User Intent: "Create BGP test: 2 ports, AS 65001/65002, 1000 pps"
             │
             + Port Mapping (from step 1)
             │
             ▼
    ┌────────────────┐
    │ Agent parses   │
    │ intent         │
    └────────────────┘
             │
             ├─ Validate protocols (BGP supported ✓)
             ├─ Validate topology (2 ports ✓)
             ├─ Validate traffic (1000 pps ✓)
             │
             ▼
    ┌──────────────────────────────────────┐
    │ Generate OTG Config:                 │
    │ - 2 ports (te1, te2 + veth mappings) │
    │ - 2 BGP devices (AS 65001/65002)     │
    │ - 2 traffic flows (1000 pps each)    │
    │ - Assertions (BGP state, packet loss)│
    └──────────────────────────────────────┘
             │
             ▼
    📤 OUTPUT: otg_config.json (OTG schema-valid)
```

### 3️⃣ **Script Generation Phase** (🟣 snappi-script-generator-agent)

```
OTG Config (from step 2)
             │
             + Infrastructure YAML
             │
             ▼
    ┌────────────────────────────┐
    │ Agent generates Python:    │
    │ - Snappi SDK setup         │
    │ - OTG config embedded      │
    │ - Protocol state polling   │
    │ - Traffic control (start/stop) │
    │ - Metrics & assertions     │
    │ - Error handling/cleanup   │
    │ - JSON report generation   │
    └────────────────────────────┘
             │
             ▼
    📤 OUTPUT: test_bgp_convergence.py
       (649 lines, production-ready, standalone)

       Usage: python test_bgp_convergence.py
       ✓ No external config files needed
       ✓ All infrastructure details embedded
       ✓ Self-contained error handling
```

---

## Parallel Execution Pattern

For **licensing cost estimation + infrastructure setup**:

```
                  User Intent
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼ (parallel)                ▼ (parallel)
    🔵 Deploy Ixia-c          🟠 Calculate License Cost
    ├─ Generate manifests     ├─ DPLU calculation (port speeds)
    ├─ Deploy infrastructure  ├─ CPLU calculation (BGP sessions)
    ├─ Validate health        ├─ Recommend tier
    │                         ├─ Cost breakdown
    │                         └─ SE disclaimer
    │                              │
    │◄─────── Both Complete ──────►│
    │
    ▼ (wait for port mapping)
    🟢 Generate Config
    └─ Inject port locations
         │
         ▼
    🟣 Generate Script
    └─ Embed infrastructure
         │
         ▼
    📤 Ready for Execution
```

---

## Existing Infrastructure Pattern

When user already has Ixia-c running at `localhost:8443`:

```
User: "I have Ixia-c at localhost:8443. Create BGP test + script."
       │
       ├─ Skip 🔵 deployment (already running)
       │
       ▼
    🟢 Generate Config
    ├─ Parse intent
    ├─ Use provided port mapping
    ├─ Generate otg_config.json
    │
    ▼
    🟣 Generate Script
    ├─ Embed controller URL (localhost:8443)
    ├─ Generate test_bgp.py
    │
    ▼
    📤 Ready to Run
       python test_bgp.py
```

---

## Licensing-Only Query

For quick cost estimation:

```
User: "What license for 4×100GE + 8 BGP sessions?"
       │
       ▼
    🟠 Licensing Agent
    ├─ Parse requirements
    ├─ Calculate DPLU (4×100GE = ?)
    ├─ Calculate CPLU (8×BGP = ?)
    ├─ Recommend tier
    │
    ▼
    📤 Cost Breakdown
       Developer: $X
       Team: $Y
       System: $Z
       Recommendation: Team tier
```

---

## Agent Composition

```
┌────────────────────────────────────────────────────────────────┐
│                   KENG OTG ORCHESTRATOR                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  🔵 ixia-c-deployment-agent                                  │
│     • Topology analysis (Docker vs Containerlab)              │
│     • Manifest generation                                     │
│     • Infrastructure deployment                              │
│     • Port mapping → downstream                              │
│                                                                │
│  🟢 otg-config-generator-agent                               │
│     • Intent classification                                   │
│     • Protocol validation                                     │
│     • OTG config generation                                   │
│     • Schema compliance (openapi.yaml)                        │
│                                                                │
│  🟣 snappi-script-generator-agent                            │
│     • Python code generation                                  │
│     • Snappi SDK integration                                  │
│     • Error handling & assertions                             │
│     • Standalone script production                            │
│                                                                │
│  🟠 keng-licensing-agent                                     │
│     • DPLU/CPLU cost calculation                             │
│     • License tier recommendation                             │
│     • Cost breakdown analysis                                │
│     • SE disclaimer inclusion                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow & Alignment

```
Deployment Phase                 Config Phase                  Script Phase
─────────────────────────────────────────────────────────────────────────

PORT MAPPING:                    OTG CONFIG:                  EMBEDDED IN
{                                {                            SCRIPT:
  "te1": "veth-a",   ──────>      "ports": [                 ──────>   import snappi
  "te2": "veth-z",               {                                      api = snappi.api()
  "controller":                    "name": "te1",                       config = snappi.Config()
    "localhost:8443"              "location": "veth-a"                 config.ports.append(...)
}                                }
                                ]                                       api.set_config(config)
                                }
                                                                        # embedded config
                                                              SCRIPT OUTPUT:
                                                              test_bgp_convergence.py
                                                              (649 lines)
```

---

## Error Recovery & Validation

```
Each Phase Validates:

🔵 Deployment
   └─ Is controller reachable? (health check)
   └─ Are all ports discoverable? (port check)
   └─ Correct port mapping format? (validation)

🟢 Config
   └─ Does OTG validate? (schema check)
   └─ Do ports align with deployment? (alignment check)
   └─ Protocols supported? (feature check)

🟣 Script
   └─ Valid Python syntax? (syntax check)
   └─ Snappi imports correct? (import check)
   └─ Error handling present? (robustness check)

🟠 Licensing
   └─ Cost calculations correct? (math check)
   └─ Tier recommendation justified? (logic check)
   └─ SE disclaimer included? (compliance check)
```

---

## Workflow Summary

| Intent | Agents | Sequence | Output |
|--------|--------|----------|--------|
| Deploy only | 🔵 | Sequential | docker-compose.yml, port mapping |
| Config only | 🟢 | - | otg_config.json |
| Script only | 🟣 | - | test_xxx.py |
| License check | 🟠 | - | Cost estimate + recommendation |
| Deploy + Config + Script | 🔵→🟢→🟣 | Sequential | Full pipeline ready |
| Deploy + License | 🔵\|🟠 | Parallel | Both outputs |
| Existing Infra + Script | 🟢→🟣 | Sequential | otg_config.json + test_xxx.py |
| Full greenfield | 🔵→🟢→🟣+🟠 | Seq + Parallel | Complete test package |

---

## References

- **AGENT_ORCHESTRATION_PLAN.md** — Detailed orchestration patterns
- **invoking_subagents.md** — Agent invocation guide
- **.claude/agents/README.md** — Agent specifications
- **/show-agents** — Agent details
- **/show-skills** — Skill overview
- **/examples** — Workflow examples
