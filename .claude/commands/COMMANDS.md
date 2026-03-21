# Claude Commands — Help & Discovery (Section C)

Complete index of all Help & Discovery commands for the KENG OTG Traffic Testing Pipeline.

---

## 📋 Section C: Help & Discovery Commands (7 Commands)

Commands designed to help users explore, learn, and understand the plugin.

### 🆘 Help & Overview

#### `/keng-help`
**Overview and quick start guide for the entire plugin.**

- Plugin summary (what is KENG/OTG)
- Quick start (3-step onboarding)
- The 5 skills table
- The 4 agents overview
- Common workflows
- Discovery commands list
- Key concepts (port alignment, standalone scripts)
- Session flow diagram
- Troubleshooting quick reference
- Documentation index

**Use when:** User is new to plugin, needs onboarding

---

### 🔍 Discovery Commands

#### `/show-skills`
**List all 5 production-ready skills with descriptions and use cases.**

- 5 skills with emoji identifiers
- Description of each (what it does, when to use)
- Input/output for each skill
- Quick start examples
- Skill directory structure
- Next steps (workflow patterns)

**Use when:** User wants to know what skills are available

---

#### `/show-agents`
**List all 4 intelligent subagents and their responsibilities.**

- 4 agents with colored circles (🔵🟢🟣🟠)
- Role and responsibilities for each
- Invocation syntax
- Success criteria
- Orchestration patterns (sequential, parallel, skip deployment)
- Orchestrator decision tree
- Agent evaluation framework overview
- Links to detailed agent specs

**Use when:** User wants to understand agent architecture and orchestration

---

#### `/show-architecture`
**Display orchestration architecture and workflow diagrams.**

- System architecture diagram (orchestrator → intent → agents)
- Greenfield pipeline (3 phases)
- Parallel execution pattern
- Existing infrastructure pattern
- Licensing-only pattern
- Agent composition block diagram
- Data flow and alignment diagram
- Error recovery and validation
- Workflow summary table

**Use when:** User wants visual understanding of system design

---

### 📚 Documentation Commands

#### `/examples`
**Workflow examples by use case (8 real-world scenarios).**

- Example 1: Greenfield BGP test (deploy + config + script)
- Example 2: Quick license check
- Example 3: IxNetwork migration
- Example 4: Existing infrastructure + custom test
- Example 5: Multi-protocol complex test
- Example 6: Parallel execution (licensing + deployment)
- Example 7: Performance baseline test
- Example 8: Minimal validation test
- Quick reference table
- Decision tree for scenario matching

**Use when:** User needs to see how to use plugin for their specific use case

---

#### `/skill-help`
**Detailed skill documentation and quick reference.**

Complete documentation for each skill:
- What it does
- When to use
- Input/output formats
- Example usage
- Supported protocols/features
- Unsupported features
- Output files and formats

**Includes:**
1. ixnetwork-to-keng-converter (conversion + feasibility)
2. otg-config-generator (intent → OTG JSON)
3. snappi-script-generator (OTG → Python)
4. ixia-c-deployment (infrastructure provisioner)
5. keng-licensing (cost + recommendations)

**Use when:** User needs detailed skill documentation

---

#### `/eval-agents`
**Agent evaluation framework and test cases.**

- Framework overview (5 questions per agent, 20 total)
- Evaluation scope (happy path, edge cases, complexity, error handling, real-world)
- 5 evaluations per agent:
  - 🔵 ixia-c-deployment-agent (deployment, topology selection, validation, errors)
  - 🟢 otg-config-generator-agent (BGP, multi-protocol, alignment, ambiguity, assertions)
  - 🟣 snappi-script-generator-agent (standalone, error handling, state polling, metrics, cleanup)
  - 🟠 keng-licensing-agent (POC, tier comparison, complex calcs, optimization, disclaimers)
- Scoring system and quality metrics
- How to run evaluations manually

**Use when:** User wants to understand agent quality, run evaluations, or understand testing framework

---

## Command Summary Table

| Command | Type | Purpose | Use When |
|---------|------|---------|----------|
| `/keng-help` | Overview | Plugin help & quick start | New user or general help |
| `/show-skills` | Discovery | List 5 skills | Want to know available skills |
| `/show-agents` | Discovery | List 4 agents | Want to understand orchestration |
| `/show-architecture` | Discovery | Architecture diagrams | Want visual system design |
| `/examples` | Documentation | Workflow scenarios | Need to use plugin for specific case |
| `/skill-help` | Documentation | Detailed skill docs | Need in-depth skill documentation |
| `/eval-agents` | Documentation | Evaluation framework | Want to understand testing/quality |

---

## Command Access Patterns

### New User Onboarding Path
```
1. /keng-help          ← Start here for overview
2. /show-skills        ← See what's available
3. /examples           ← Find your use case
4. @agent-name ...     ← Invoke agent
```

### Deep Dive Path
```
1. /show-agents        ← Understand architecture
2. /show-architecture  ← See workflows visually
3. /eval-agents        ← Understand quality framework
4. /skill-help         ← Study detailed docs
```

### Quick Reference Path
```
/keng-help             ← Troubleshooting section
/examples              ← Quick reference table
/show-agents           ← Decision tree
```

---

## Next Phases (Sections A & B)

### Section A: Essential Skill Shortcuts
Commands for quick invocation of skills:
- `/otg-gen` — Quick OTG config generation
- `/snappi-script` — Quick script generation
- `/deploy-ixia` — Quick Ixia-c deployment
- `/licensing` — Quick licensing check
- `/migrate-ix` — Quick IxNetwork migration

### Section B: Workflow Commands
Commands for full end-to-end workflows:
- `/create-test` — Full test creation pipeline
- `/quick-bgp-test` — BGP test shortcut
- `/migrate-and-run` — IxNetwork migration + execution
- `/check-licensing` — Licensing evaluation workflow

---

## File Structure

```
.claude/commands/
├── COMMANDS.md                    # This file (index)
├── keng-help.md                   # Plugin help
├── show-skills.md                 # Skill discovery
├── show-agents.md                 # Agent discovery
├── show-architecture.md           # Architecture diagrams
├── examples.md                    # Workflow examples
├── skill-help.md                  # Detailed skill docs
└── eval-agents.md                 # Evaluation framework
```

---

## Key Features of Section C

✓ **Comprehensive Help** — keng-help covers plugin overview and quick start
✓ **Discovery** — show-skills, show-agents, show-architecture help users navigate
✓ **Real-World Examples** — 8 scenarios covering common use cases
✓ **Detailed Docs** — skill-help and eval-agents for deep dives
✓ **Progressive Disclosure** — From overview → discovery → details
✓ **Multiple Entry Points** — Users can start wherever they need

---

## Usage Statistics

- **7 commands** in Section C
- **50+ pages** of detailed documentation
- **8 real-world examples**
- **20 evaluation scenarios**
- **5 skill overviews**
- **4 agent specifications**
- **6 architecture diagrams**

---

## Next Steps

1. **Build Section A:** Essential Skill Shortcuts
   - /otg-gen, /snappi-script, /deploy-ixia, /licensing, /migrate-ix

2. **Build Section B:** Workflow Commands
   - /create-test, /quick-bgp-test, /migrate-and-run, /check-licensing

3. **Create Plugin Manifest:** plugin.json with command definitions

4. **Package for Distribution:** Final plugin package ready for Claude Code Marketplace

---

## See Also

- **CLAUDE.md** — Project guidance for Claude Code
- **AGENT_ORCHESTRATION_PLAN.md** — Detailed orchestration patterns
- **invoking_subagents.md** — Subagent invocation guide
- **.claude/agents/README.md** — Agent specifications
- **.claude/skills/INDEX.md** — Skill index
