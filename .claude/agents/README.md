# OTG Subagent Specifications

This directory contains agent specifications for the OTG test pipeline orchestration. Each agent is a specialized worker that handles one phase of the test lifecycle.

## Agents Overview

### 1. 🔵 **ixia-c-deployment-agent** (`ixia-c-deployment-agent.md`)
**Role:** Infrastructure Provisioner
**Input:** Deployment method, use case, port count, protocols
**Output:** `docker-compose.yml` or `topo.clab.yml`, controller URL, port mapping
**Use when:** You need to deploy Ixia-c infrastructure (Docker or Containerlab)

```
Example: "Deploy Ixia-c for BGP testing with Docker Compose"
Output: docker-compose.yml + port map (te1:location_1:5555, te2:location_2:5556)
```

---

### 2. 🟢 **otg-config-generator-agent** (`otg-config-generator-agent.md`)
**Role:** Intent → OTG Configuration
**Input:** Natural language test intent, infrastructure details (from agent 1)
**Output:** `otg_config.json` with ports, devices, protocols, flows, assertions
**Use when:** You need to convert test descriptions into structured OTG configurations

```
Example: "BGP convergence test, 2 ports, AS 65001/65002, 1000 pps, bidirectional"
Output: otg_config.json (aligned with infrastructure)
```

---

### 3. 🟣 **snappi-script-generator-agent** (`snappi-script-generator-agent.md`)
**Role:** Executor (OTG Config → Runnable Script)
**Input:** `otg_config.json`, infrastructure YAML
**Output:** `test_*.py` (standalone Python Snappi script)
**Use when:** You need a production-ready, executable test script

```
Example: "Generate Snappi script from otg_config.json, controller at localhost:8443"
Output: test_bgp_convergence.py (ready to run: python test_bgp_convergence.py)
```

---

### 4. 🟠 **keng-licensing-agent** (`keng-licensing-agent.md`)
**Role:** Licensing Advisor (Parallel or Pre-Flight)
**Input:** Test config (ports, speeds, protocols, sessions)
**Output:** License recommendation, cost estimate, tier comparison
**Use when:** You need to understand licensing costs before committing to a design

```
Example: "I'm planning 2×100GE + 4 BGP sessions. What license do I need?"
Output: Licensing tier recommendation + cost breakdown + SE disclaimer
```

---

### 5. 🔴 **ixnetwork-to-keng-converter-agent** (`ixnetwork-to-keng-converter-agent.md`)
**Role:** IxNetwork Migration Specialist
**Input:** IxNetwork RestPy code, JSON config, or high-level description
**Output:** Feasibility report + converted OTG JSON config + conversion report
**Use when:** You need to migrate existing IxNetwork tests to OTG/KENG format

```
Example: "Convert this IxNetwork BGP config to OTG format"
Output: conversion_report.md + converted_config.json (OTG-compliant)
```

---

## Command → Agent → Skill Hierarchy

All Section A slash commands dispatch to agents, which in turn invoke skills:

```
/kengotg-deploy-ixia    → ixia-c-deployment-agent          → ixia-c-deployment skill
/kengotg-otg-gen        → otg-config-generator-agent       → otg-config-generator skill
/kengotg-snappi-script  → snappi-script-generator-agent    → snappi-script-generator skill
/kengotg-licensing      → keng-licensing-agent              → keng-licensing skill
/kengotg-migrate-ix     → ixnetwork-to-keng-converter-agent → ixnetwork-to-keng-converter skill
```

**Why this hierarchy?**
- **Commands** provide user-friendly entry points with defaults and examples
- **Agents** run in isolated context, manage their own memory, and invoke skills
- **Skills** contain the technical implementation and reference material

---

## Sequential Workflow (Use Case 1: Full Pipeline)

```
User Intent
  │
  ├─ 🔵 ixia-c-deployment-agent
  │  └─ Output: docker-compose.yml, port_map
  │
  ├─ 🟢 otg-config-generator-agent
  │  ├─ Input: Natural language + port_map
  │  └─ Output: otg_config.json
  │
  ├─ 🟣 snappi-script-generator-agent
  │  ├─ Input: otg_config.json + infrastructure
  │  └─ Output: test_*.py
  │
  └─ 🟠 keng-licensing-agent (parallel, optional)
     └─ Output: License recommendation + cost
```

---

## Parallel Workflow (Use Case 6: Full Pipeline + Licensing)

```
User Intent
  │
  ├─ 🔵 ixia-c-deployment-agent ────┐
  │                                   ├─ Run in parallel
  └─ 🟠 keng-licensing-agent ────────┘
       (both independent)
  │
  ├─ 🟢 otg-config-generator-agent (waits for infra output)
  │  │
  │  └─ 🟣 snappi-script-generator-agent (sequential)
```

---

## Standalone Workflows

### Only Deployment
> "Just deploy Ixia-c for BGP testing"
- Use: 🔵 ixia-c-deployment-agent only

### Only Licensing Question
> "License cost for 4×100GE + 8 BGP sessions?"
- Use: 🟠 keng-licensing-agent only

### Config + Script (Existing Infrastructure)
> "I have Ixia-c at localhost:8443. Create BGP config and script."
- Use: 🟢 otg-config-generator-agent → 🟣 snappi-script-generator-agent (skip deployment)

### Script Only (Existing OTG Config)
> "Generate Snappi script from my otg_config.json"
- Use: 🟣 snappi-script-generator-agent only

---

## Key Characteristics

| Aspect | Details |
|--------|---------|
| **Format** | YAML frontmatter + Markdown documentation |
| **Model** | Sonnet (high quality, handles complex tasks) |
| **Permissions** | `acceptAll` (agents can create/edit files) |
| **Tools** | Bash, Read, Write, Edit, Glob, Grep, Task, WebFetch, WebSearch |
| **Skills** | Each agent wraps a corresponding skill (ixia-c-deployment, otg-config-generator, snappi-script-generator, keng-licensing, ixnetwork-to-keng-converter) |
| **Max Turns** | 10 (allow for iterative refinement) |

---

## Invocation Examples

### From Claude Code main session
```bash
# The orchestrator (you) dispatches subagents based on user intent
# Example: User says "Create a BGP test, deploy with Docker, generate script"

# Step 1: Dispatch ixia-c-deployment-agent
@ixia-c-deployment-agent Deploy Ixia-c for BGP with Docker Compose

# Step 2: Dispatch otg-config-generator-agent (with infra output)
@otg-config-generator-agent Create BGP config: 2 ports, AS 65001/65002, 1000 pps

# Step 3: Dispatch snappi-script-generator-agent (with config + infra)
@snappi-script-generator-agent Generate script from otg_config.json, controller at localhost:8443
```

---

## Design Principles

1. **Single Responsibility** — Each agent owns one phase of the pipeline
2. **Data Handoff** — Outputs from one agent are inputs to the next (deployment → config → script)
3. **Standalone Capable** — Each agent can be invoked independently for specific tasks
4. **Production-Ready** — All outputs are validated, documented, and immediately actionable
5. **Error Handling** — Agents gracefully handle missing inputs, validate outputs, provide clear next steps
6. **Orchestrator Role** — Claude Code (you) decide when and how to invoke agents based on user intent

---

## References

- **Orchestration Plan:** `AGENT_ORCHESTRATION_PLAN.md`
- **Skill Definitions:** Available via `/agents list` in Claude Code
- **Format Template:** Based on weather-agent pattern from claude-code-best-practice

---

## Version & Status

- **Created:** 2026-03-19
- **Status:** Initial spec complete ✅
- **Skills integrated:** ✅ ixia-c-deployment, otg-config-generator, snappi-script-generator, keng-licensing, ixnetwork-to-keng-converter
- **Agents:** 5 (was 4 — added ixnetwork-to-keng-converter-agent)
- **Ready for:** Production use, orchestration patterns
