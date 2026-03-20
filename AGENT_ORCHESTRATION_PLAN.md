# OTG Sub-Agent Orchestration Plan

**Claude Code as orchestrator** — You provide intent; sub-agents execute specialized tasks.

This plan excludes the `ixnetwork-to-keng-converter` skill. All flows are **greenfield** (natural language → OTG) or **infrastructure-first**.

---

## Sub-Agent Mapping

| Skill | Sub-Agent Role | Input | Output |
|-------|----------------|-------|--------|
| **ixia-c-deployment** | Infrastructure deployer | Deployment type (Docker Compose, Containerlab), protocol needs | `docker-compose.yml` / `topo.clab.yml`, controller URL, port `location` values |
| **otg-config-generator** | Intent → OTG config | Natural language test scenario | `otg_config.json` |
| **snappi-script-generator** | Config → executable script | OTG JSON + infrastructure YAML | `test_*.py` (standalone Snappi script) |
| **keng-licensing** | Licensing advisor | Test config (ports, protocols, sessions) | License recommendation, cost estimate, disclaimer |

---

## Orchestration Use Cases

### Use Case 1: Full Greenfield Test (Deploy + Config + Script)

**User intent:**
> "Create a BGP convergence test with 2 ports, AS 65001 and 65002, bidirectional traffic at 1000 pps. Deploy Ixia-c with Docker Compose and give me a runnable script."

**Orchestrator flow:**

```
User Intent
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (Claude Code)                                       │
│ 1. Parse: greenfield BGP test, 2 ports, Docker Compose           │
│ 2. Dispatch: deployment → config → script (sequential)           │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─► Subagent 1: ixia-c-deployment
    │   Input: "Docker Compose CP+DP, 2 ports for BGP"
    │   Output: docker-compose.yml, location_map, port locations (te1:5555, te2:5556)
    │
    ├─► Subagent 2: otg-config-generator
    │   Input: "2 ports, BGP AS 65001/65002, bidirectional 1000 pps"
    │   Output: otg_config.json (port names aligned with deployment)
    │   (Orchestrator injects port locations from Subagent 1 into config)
    │
    └─► Subagent 3: snappi-script-generator
        Input: otg_config.json + infrastructure.yaml (controller URL, port locations from Subagent 1)
        Output: test_bgp_convergence.py
```

**Overarching intent template:**
```
Create a complete OTG test from scratch:
- Test scenario: [natural language, e.g. "BGP with 2 ports, AS 65001/65002, 1000 pps"]
- Deployment: Docker Compose (B2B | CP+DP | LAG) | Containerlab
- Output: deployment config + OTG config + runnable Snappi script
```

---

### Use Case 2: Config + Script Only (Existing Infrastructure)

**User intent:**
> "I have Ixia-c running at localhost:8443. Create a BGP test with 2 ports and give me a Snappi script."

**Orchestrator flow:**

```
User Intent
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                    │
│ 1. Parse: existing infra, config + script only                  │
│ 2. Skip deployment; dispatch config → script                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─► Subagent 1: otg-config-generator
    │   Input: "2 ports, BGP AS 65001/65002"
    │   Output: otg_config.json
    │
    └─► Subagent 2: snappi-script-generator
        Input: otg_config.json + infrastructure (localhost:8443, port locations)
        Output: test_bgp.py
```

**Overarching intent template:**
```
Generate OTG config and script (no deployment):
- Test scenario: [natural language]
- Infrastructure: Ixia-c at [URL] or localhost:8443, ports [e.g. eth1, eth2]
- Output: otg_config.json + test_*.py
```

---

### Use Case 3: Deployment Only

**User intent:**
> "Set up Ixia-c for BGP testing with Docker Compose."

**Orchestrator flow:**

```
User Intent
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                    │
│ 1. Parse: deployment only, BGP = need CP+DP                    │
│ 2. Dispatch: ixia-c-deployment                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    └─► Subagent: ixia-c-deployment
        Input: "Docker Compose CP+DP for BGP"
        Output: docker-compose.yml, verification commands, port locations
```

**Overarching intent template:**
```
Deploy Ixia-c:
- Method: Docker Compose (B2B | CP+DP | LAG) | Containerlab
- Use case: [traffic-only | BGP/ISIS | LAG testing]
- Output: deployment files + verification steps
```

---

### Use Case 4: Script from Existing OTG Config

**User intent:**
> "I have otg_config.json. Generate a Snappi script for it. Controller at 192.168.1.100:8443."

**Orchestrator flow:**

```
User Intent
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                    │
│ 1. Parse: existing OTG config, need script only                 │
│ 2. Dispatch: snappi-script-generator                            │
└─────────────────────────────────────────────────────────────────┘
    │
    └─► Subagent: snappi-script-generator
        Input: otg_config.json (path or inline) + infrastructure.yaml
        Output: test_*.py
```

**Overarching intent template:**
```
Generate Snappi script from existing OTG config:
- Config: [path or paste otg_config.json]
- Infrastructure: controller [URL], ports [locations]
- Assertions: [optional]
- Output: test_*.py
```

---

### Use Case 5: Licensing Estimate (Standalone or Pre-Flight)

**User intent:**
> "I'm planning a test with 2×100GE ports and 4 BGP sessions. Which license do I need?"

**Orchestrator flow:**

```
User Intent
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                    │
│ 1. Parse: licensing question                                    │
│ 2. Dispatch: keng-licensing                                    │
└─────────────────────────────────────────────────────────────────┘
    │
    └─► Subagent: keng-licensing
        Input: 2×100GE, 4 BGP sessions, [Developer | Team | System]
        Output: License recommendation, cost estimate, SE disclaimer
```

**Overarching intent template:**
```
Estimate KENG licensing:
- Test config: [ports, speeds, protocols, session counts]
- License tier: Developer | Team | System
- Output: recommendation + cost estimate + disclaimer
```

---

### Use Case 6: Full Pipeline + Licensing Check

**User intent:**
> "Create a BGP test with 2×100GE and 4 BGP sessions. Deploy with Docker, generate the script, and tell me the license cost."

**Orchestrator flow:**

```
User Intent
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                    │
│ 1. Parse: full pipeline + licensing                             │
│ 2. Dispatch: keng-licensing in parallel with deployment        │
│ 3. Then: otg-config-generator → snappi-script-generator        │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─► Subagent A (parallel): keng-licensing
    │   Input: 2×100GE, 4 BGP sessions
    │   Output: License recommendation
    │
    ├─► Subagent B: ixia-c-deployment
    │   Output: docker-compose.yml, port locations
    │
    ├─► Subagent C: otg-config-generator
    │   Input: "2 ports, 4 BGP sessions, 2×100GE"
    │   Output: otg_config.json
    │
    └─► Subagent D: snappi-script-generator
        Input: otg_config.json + infrastructure
        Output: test_*.py
```

**Overarching intent template:**
```
Full pipeline with licensing:
- Test scenario: [natural language]
- Deployment: [Docker | Containerlab]
- Include: license estimate
- Output: deployment + config + script + licensing recommendation
```

---

## Intent Classification Matrix

| User says | Orchestrator invokes |
|-----------|----------------------|
| "Create a BGP test and deploy Ixia-c" | ixia-c-deployment → otg-config-generator → snappi-script-generator |
| "I have Ixia-c; create a BGP test and script" | otg-config-generator → snappi-script-generator |
| "Deploy Ixia-c for BGP testing" | ixia-c-deployment |
| "Generate script from my otg_config.json" | snappi-script-generator |
| "How much will 2×100GE + 4 BGP cost?" | keng-licensing |
| "Full BGP test + deploy + license estimate" | keng-licensing (parallel) + ixia-c-deployment → otg-config-generator → snappi-script-generator |

---

## Orchestrator Responsibilities

1. **Intent parsing** — Classify: full pipeline, config-only, deployment-only, script-only, licensing.
2. **Subagent selection** — Choose which skills to invoke and in what order.
3. **Data handoff** — Pass outputs between subagents (e.g. `location_map` → OTG config → infrastructure YAML).
4. **Parallel vs sequential** — Run keng-licensing in parallel when appropriate; keep config → script sequential.
5. **Clarification** — Ask for missing details (port locations, controller URL, deployment type) before dispatching.

---

## One-Liner Intent Examples

| Intent | Subagents |
|--------|-----------|
| "BGP test, 2 ports, deploy with Docker, give me script" | ixia-c-deployment → otg-config-generator → snappi-script-generator |
| "LAG test with LACP, Containerlab, full pipeline" | ixia-c-deployment → otg-config-generator → snappi-script-generator |
| "I have ixia-c at 10.0.0.1; BGP test + script" | otg-config-generator → snappi-script-generator |
| "Just deploy Ixia-c for protocols" | ixia-c-deployment |
| "Script from bgp_config.json, localhost:8443" | snappi-script-generator |
| "License cost for 4×100GE + 8 BGP" | keng-licensing |

---

## Version

- **Created:** March 2026
- **Excludes:** ixnetwork-to-keng-converter
- **Skills:** ixia-c-deployment, otg-config-generator, snappi-script-generator, keng-licensing
