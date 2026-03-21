# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**KENG OTG Traffic Testing Pipeline** — A vendor-neutral network test automation toolkit that:
- Converts IxNetwork configs → OTG (Open Traffic Generator) format
- Generates OTG configurations from natural language intent
- Generates production-ready Snappi scripts from OTG configs
- Deploys and configures Ixia-c infrastructure (Docker Compose, Containerlab)
- Advises on OTG licensing costs and recommendations

**5 Production-Ready Skills:**
1. **ixnetwork-to-keng-converter** — IxNetwork → OTG config migration
2. **otg-config-generator** — Natural language → OTG config
3. **snappi-script-generator** — OTG config → executable Python script
4. **ixia-c-deployment** — Infrastructure provisioning (Docker, Containerlab)
5. **keng-licensing** — Licensing recommendations & cost estimation

**4 Intelligent Subagents:**
1. 🔵 **ixia-c-deployment-agent** — Infrastructure provisioner
2. 🟢 **otg-config-generator-agent** — Intent → config translator
3. 🟣 **snappi-script-generator-agent** — Config → script executor
4. 🟠 **keng-licensing-agent** — Licensing advisor

**16 Claude Commands (3 sections):**
- **Section C (Help & Discovery):** 7 commands — Onboarding, skill discovery, architecture overview
- **Section A (Skill Shortcuts):** 5 commands — Quick wrappers around skills with sensible defaults
- **Section B (Workflows):** 4 commands — End-to-end workflows orchestrating multiple agents

---

## Architecture & Orchestration Model

### Skill-Based Architecture
The project is organized around **skills** (`.claude/skills/`), not traditional code modules. Each skill is:
- **Self-contained**: Owns its own logic, references, test cases
- **Composable**: Can be invoked independently or chained with others
- **Documented**: SKILL.md (technical), README.md (user guide), evals.json (test cases)

### Subagent Orchestration Pattern
Claude Code acts as an **orchestrator** that:
1. **Parses user intent** — Classify whether user wants deployment, config, script, or licensing
2. **Dispatches to subagents** — Invoke specialized agents (`.claude/agents/`) for each phase
3. **Manages data handoff** — Output from agent N feeds into agent N+1
4. **Handles parallelism** — Run independent tasks (e.g., licensing + deployment) in parallel

**Subagents (in `.claude/agents/`):**
- 🔵 **ixia-c-deployment-agent** — Infrastructure provisioner
- 🟢 **otg-config-generator-agent** — Intent → config translator
- 🟣 **snappi-script-generator-agent** — Config → script executor
- 🟠 **keng-licensing-agent** — Licensing advisor

### Standard Workflows
```
Full pipeline:       deployment → config → script + licensing (parallel)
Config only:        config → script
Deployment only:    deployment alone
Licensing check:    licensing alone
```

See **AGENT_ORCHESTRATION_PLAN.md** for detailed use cases and orchestration flows.

---

## Key Concepts

### Intent Classification
User intents fall into these patterns:
- **Greenfield**: "Create BGP test + deploy + script" → all 3 subagents sequentially
- **Existing infrastructure**: "I have ixia-c at localhost:8443; create config + script" → skip deployment
- **Config only**: "Generate OTG config from my test scenario" → only otg-config-generator
- **Licensing question**: "What license for 4×100GE + 8 BGP?" → only keng-licensing
- **IxNetwork migration**: "Convert this IxNetwork config" → ixnetwork-to-keng-converter skill

### Port Mapping & Alignment
Critical pattern: **Deployment outputs port locations** that must be **injected into OTG config**:
- ixia-c-deployment-agent returns: `{"te1": "location_1:5555", "te2": "location_2:5556", ...}`
- otg-config-generator-agent consumes these and aligns port names with locations
- snappi-script-generator-agent uses aligned config to generate scripts
- **Never proceed without alignment** — Downstream agents depend on correct port locations

### Standalone vs. Integrated Scripts
**Snappi scripts are standalone**: No external dependencies except `snappi` SDK. All OTG config and infrastructure details are embedded.
**Advantage**: Users can copy script and run immediately: `python test_xxx.py`

---

## File Structure & Key Locations

```
kengotg/
├── README.md                           ← Project overview (start here for users)
├── AGENT_ORCHESTRATION_PLAN.md         ← Detailed orchestration patterns
├── openapi.yaml                        ← OTG schema reference (required by skills)
├── bgp_keng.json                       ← Example OTG config output
│
└── .claude/
    ├── settings.local.json             ← Claude Code workspace settings
    │
    ├── commands/                       ← Claude Commands (16 total)
    │   ├── COMMANDS.md                 ← Commands index & navigation
    │   ├── kengotg-keng-help.md        ← Plugin help (Section C)
    │   ├── kengotg-show-skills.md      ← Skill discovery (Section C)
    │   ├── kengotg-show-agents.md      ← Agent discovery (Section C)
    │   ├── kengotg-show-architecture.md ← Architecture diagrams (Section C)
    │   ├── kengotg-examples.md         ← Workflow examples (Section C)
    │   ├── kengotg-skill-help.md       ← Detailed skill docs (Section C)
    │   ├── kengotg-eval-agents.md      ← Evaluation framework (Section C)
    │   ├── kengotg-otg-gen.md          ← Quick OTG gen (Section A)
    │   ├── kengotg-snappi-script.md    ← Quick script gen (Section A)
    │   ├── kengotg-deploy-ixia.md      ← Quick deployment (Section A)
    │   ├── kengotg-licensing.md        ← Quick licensing (Section A)
    │   ├── kengotg-migrate-ix.md       ← Quick migration (Section A)
    │   ├── kengotg-create-test.md      ← Full pipeline (Section B)
    │   ├── kengotg-quick-bgp-test.md   ← BGP shortcut (Section B)
    │   ├── kengotg-migrate-and-run.md  ← Migration + exec (Section B)
    │   └── kengotg-check-licensing.md  ← Licensing workflow (Section B)
    │
    ├── agents/                         ← Subagent specifications
    │   ├── README.md                   ← Agents overview & workflows
    │   ├── ixia-c-deployment-agent.md
    │   ├── otg-config-generator-agent.md
    │   ├── snappi-script-generator-agent.md
    │   ├── keng-licensing-agent.md
    │   └── eval-sets/                  ← Agent evaluation test cases
    │       ├── README.md
    │       ├── ixia-c-deployment-agent-eval.json      (5 questions)
    │       ├── otg-config-generator-agent-eval.json   (5 questions)
    │       ├── snappi-script-generator-agent-eval.json (5 questions)
    │       └── keng-licensing-agent-eval.json         (5 questions)
    │
    └── skills/                         ← Production skills
        ├── INDEX.md                    ← Skill discovery guide (START HERE)
        │
        ├── ixnetwork-to-keng-converter/
        │   ├── SKILL.md                ← Technical reference
        │   ├── README.md               ← User guide + troubleshooting
        │   ├── PRODUCTION_CHECKLIST.md
        │   └── evals/evals.json        ← 4 test scenarios
        │
        ├── otg-config-generator/
        │   ├── SKILL.md
        │   ├── README.md
        │   └── evals/evals.json
        │
        ├── snappi-script-generator/
        │   ├── SKILL.md
        │   ├── README.md
        │   ├── evals/evals.json
        │   └── references/             ← Protocol examples, assertion patterns, GitHub snippets
        │
        ├── ixia-c-deployment/
        │   ├── SKILL.md
        │   ├── README.md
        │   └── ref-*.md                ← Docker/Containerlab/veth setup references
        │
        └── keng-licensing/
            ├── SKILL.md
            └── evals.json              ← 8 test scenarios
```

---

## Claude Commands Framework (16 Total)

### What are Claude Commands?
Claude Commands (slash commands) provide quick access to plugin features without needing to invoke agents or skills directly. They guide users through common workflows with sensible defaults and helpful examples.

### Three-Tier Command Structure

#### Section C: Help & Discovery (7 commands)
**Purpose:** Onboarding, exploration, learning

```
/kengotg-keng-help          — Plugin overview & quick start
/kengotg-show-skills        — List all 5 skills
/kengotg-show-agents        — List all 4 agents & orchestration
/kengotg-show-architecture  — Architecture diagrams & patterns
/kengotg-examples           — 8 real-world workflow examples
/kengotg-skill-help         — Detailed skill documentation
/kengotg-eval-agents        — Agent evaluation framework (20 questions)
```

**Use when:** New user, need to understand plugin, need examples

#### Section A: Skill Shortcuts (5 commands)
**Purpose:** Quick wrappers around skills with sensible defaults

```
/kengotg-otg-gen            — Quick OTG config generation
/kengotg-snappi-script      — Quick Snappi script generation
/kengotg-deploy-ixia        — Quick Ixia-c deployment
/kengotg-licensing          — Quick licensing check
/kengotg-migrate-ix         — Quick IxNetwork migration
```

**Use when:** Want quick invocation with defaults, not full customization

#### Section B: Workflow Commands (4 commands)
**Purpose:** End-to-end orchestration across multiple agents

```
/kengotg-create-test        — Full pipeline (deploy→config→script)
/kengotg-quick-bgp-test     — BGP test with optimized defaults
/kengotg-migrate-and-run    — IxNetwork migration + execution
/kengotg-check-licensing    — Complete licensing evaluation
```

**Use when:** Need full workflow, orchestration of multiple steps

### Command Design Philosophy

| Aspect | Details |
|--------|---------|
| **Names** | `/kengotg-*` prefix for clarity and branding |
| **Format** | YAML frontmatter + markdown per Claude Commands spec |
| **Context** | Each command includes usage patterns, examples, troubleshooting |
| **Progression** | C → A → B (discovery → quick access → full workflows) |
| **Docs** | ~150KB total, ~10+ pages per command, highly discoverable |

### User Workflows with Commands

**New User Journey:**
```
1. /kengotg-keng-help           ← Start here
2. /kengotg-show-skills         ← See what's available
3. /kengotg-examples            ← Find a matching scenario
4. /kengotg-create-test         ← Execute full workflow
```

**Quick Test User Journey:**
```
1. /kengotg-quick-bgp-test 4 ports  ← One-liner for BGP
2. Ready to run                      ← No further setup needed
```

**Migration User Journey:**
```
1. /kengotg-migrate-ix          ← Check feasibility
2. /kengotg-migrate-and-run     ← Full migration + execution
```

**Advanced User Journey:**
```
1. /kengotg-show-architecture   ← Understand design
2. @ixia-c-deployment-agent ...  ← Invoke agents directly
3. @otg-config-generator-agent ...
```

---

## Common Development Tasks

### Understanding the Codebase
1. **Start with README.md** — High-level overview, skill descriptions, workflow examples
2. **Read AGENT_ORCHESTRATION_PLAN.md** — Orchestration patterns and use cases
3. **Explore `.claude/skills/INDEX.md`** — Technical skill overview and when to use each
4. **Reference each skill's SKILL.md** — Deep technical details for implementation

### Using Commands, Skills, and Agents

**Quick start with commands (recommended for most users):**
```bash
# Help & Discovery
/kengotg-keng-help           # Plugin overview
/kengotg-show-skills         # List all skills
/kengotg-examples            # See workflow examples

# Quick shortcuts
/kengotg-otg-gen             # Generate OTG config (with defaults)
/kengotg-deploy-ixia         # Deploy infrastructure (with defaults)

# Full workflows
/kengotg-create-test         # End-to-end pipeline
/kengotg-quick-bgp-test      # BGP test shortcut
/kengotg-migrate-and-run     # IxNetwork migration + execution
```

**Direct skill invocation (when you need full control):**
```bash
# Skills with customization
/ixnetwork-to-keng-converter  (paste IxNetwork config)
/otg-config-generator         (natural language intent + parameters)
/snappi-script-generator      (OTG config + infrastructure YAML)
/ixia-c-deployment            (deployment requirements + topology choice)
/keng-licensing               (licensing question + details)
```

**Agent invocation (for complex orchestration):**
```bash
# Invoke agents directly for full control
@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose for BGP...
@otg-config-generator-agent Create BGP test with 2 ports, AS 65001/65002...
@snappi-script-generator-agent Generate test script from bgp_config.json...
@keng-licensing-agent What license for 4×100GE + 8 BGP sessions?
```

**View test cases:**
```bash
cat .claude/skills/ixnetwork-to-keng-converter/evals/evals.json
cat .claude/agents/eval-sets/ixia-c-deployment-agent-eval.json
```

### Evaluating Agent Quality
```bash
# Open agent spec to understand responsibilities
cat .claude/agents/ixia-c-deployment-agent.md

# Review evaluation set (5 questions per agent)
cat .claude/agents/eval-sets/ixia-c-deployment-agent-eval.json

# Run an eval question by invoking agent with the scenario
# Assess outputs against success_criteria in eval JSON
```

### Adding a New Use Case / Workflow
1. **Document intent pattern** — Add to AGENT_ORCHESTRATION_PLAN.md under "Intent Classification Matrix"
2. **Identify agent dispatch sequence** — Update orchestration flow diagram
3. **Update subagent specs** if new input/output patterns needed
4. **Add eval questions** if testing new scenarios

### Modifying a Skill
1. **Read SKILL.md** — Understand current implementation and constraints
2. **Check evals.json** — Understand expected inputs/outputs and test cases
3. **Modify the skill logic** (usually in the skill's instructions/prompt)
4. **Update README.md** if user-facing behavior changes
5. **Add eval cases** for new scenarios

---

## Critical Patterns & Best Practices

### Port Location Alignment
**Never skip port alignment validation:**
- After deployment: Agent must return `port_mapping` with all locations
- Before config generation: Validate port_mapping matches port count in intent
- Before script generation: Ensure config ports align with infrastructure ports
- Failure to align = scripts fail at runtime (connection errors)

### Standalone Script Generation
**Snappi scripts must be self-contained:**
- All infrastructure details (controller URL, ports, credentials) embedded in script
- No external config files required
- Users should be able to run: `python test_xxx.py` immediately
- Dependencies: only `snappi` SDK (installed via pip)

### Error Handling in Agents
**Agents must be resilient:**
- Validate all inputs (port counts, speeds, protocol support)
- Provide clear error messages (not silent failures)
- Ask for clarification on ambiguous intent (don't guess)
- Fail gracefully with actionable next steps

### Data Validation
**Always validate generated outputs:**
- OTG configs: Validate against openapi.yaml schema
- Scripts: Validate Python syntax, Snappi imports
- Port mapping: Verify no nulls, consistent format
- Licensing: Verify cost calculations, include disclaimers

---

## Orchestrator Decision Points

### When to Dispatch Which Agent

**User says: "Deploy Ixia-c for BGP testing"**
→ Only ixia-c-deployment-agent (deployment only)

**User says: "Create a BGP test and deploy"**
→ ixia-c-deployment-agent → otg-config-generator-agent → snappi-script-generator-agent (sequential)

**User says: "I have Ixia-c at localhost:8443; create a BGP test"**
→ Skip ixia-c-deployment-agent; go to otg-config-generator-agent → snappi-script-generator-agent

**User says: "What license for 4×100GE + 8 BGP?"**
→ Only keng-licensing-agent

**User says: "Create full test + tell me the license cost"**
→ Run keng-licensing-agent in parallel with deployment → config → script

### Before Dispatching
1. **Classify intent** — Is it greenfield, existing-infra, licensing, or migration?
2. **Ask clarifications** — Missing port count? Protocol details? Infrastructure URL?
3. **Determine sequence** — Serial (deployment→config→script) or parallel (licensing + infrastructure)?
4. **Prepare inputs** — What data does each agent need from previous agents?

---

## Alignment with User Preferences

From CLAUDE.md at `/Users/ashwin.joshi/.claude/CLAUDE.md` (global preferences):

**Role:** Senior Software Engineer + Network Automation Architect
**Optimize for:** Correctness, clarity, reproducibility, scalability
**Assume:** Strong Python, deep networking background, comfortable with Docker/Containerlab/REST APIs/CI-CD

**When debugging:**
- Identify root cause (protocol/auth/infra/state)
- Be deterministic (not generic checklists)
- Surface actionable solutions

**When writing code:**
- Prefer clarity over cleverness
- Use guard clauses & early returns
- Use type hints, Pydantic for structured data
- Fail fast, validate at boundaries

---

## References & Important Files

- **README.md** — Project overview, workflow examples, skill descriptions
- **AGENT_ORCHESTRATION_PLAN.md** — Detailed orchestration patterns, use cases, decision tree
- **.claude/skills/INDEX.md** — Skill technical overview
- **.claude/agents/README.md** — Subagent specs, workflows, when to invoke each
- **.claude/agents/eval-sets/README.md** — Agent evaluation framework
- **openapi.yaml** — OTG schema (required by skills for validation)

---

## Status & Version

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| **Project** | 2.0 | Production-Ready | 5 skills, 4 agents, 16 commands, full plugin |
| **Skills** (5) | 1.1 | ✅ Ready | All production-ready with eval tests |
| ├─ ixnetwork-to-keng-converter | 1.0 | ✅ Ready | Feasibility analysis + conversion |
| ├─ otg-config-generator | 1.0 | ✅ Ready | Natural language → OTG config |
| ├─ snappi-script-generator | 1.1 | ✅ Ready | OTG config → executable script |
| ├─ ixia-c-deployment | 1.0 | ✅ Ready | Docker Compose, Containerlab |
| └─ keng-licensing | 1.0 | ✅ Ready | Cost calc + recommendations |
| **Subagents** (4) | 1.0 | ✅ Ready | 20 evaluation questions |
| ├─ ixia-c-deployment-agent | 1.0 | ✅ Ready | Infrastructure provisioner |
| ├─ otg-config-generator-agent | 1.0 | ✅ Ready | Intent → config translator |
| ├─ snappi-script-generator-agent | 1.0 | ✅ Ready | Config → script executor |
| └─ keng-licensing-agent | 1.0 | ✅ Ready | Licensing advisor |
| **Commands** (16) | 1.0 | ✅ Ready | 150KB documentation, 3 tiers |
| ├─ Section C (Help) | 1.0 | ✅ Ready | 7 discovery commands |
| ├─ Section A (Shortcuts) | 1.0 | ✅ Ready | 5 quick-access commands |
| └─ Section B (Workflows) | 1.0 | ✅ Ready | 4 end-to-end commands |
| **Orchestration** | 1.0 | ✅ Ready | 6 use cases, parallel dispatch |
| **Documentation** | 2.0 | ✅ Ready | 500+ KB total, highly discoverable |
