---
name: kengotg-list-commands
description: Show all 16 available Claude Commands organized by section (Help, Shortcuts, Workflows)
disable-model-invocation: false
allowed-tools: []
---

# All KENG OTG Commands (16 Total)

Complete reference to all available commands in the KENG OTG Traffic Testing Pipeline, organized in three tiers.

---

## 📚 Section C: Help & Discovery (7 Commands)

### Overview & Onboarding

#### 🆘 `/kengotg-keng-help`
**Plugin overview and quick start guide for the entire plugin.**

- Plugin summary and core concepts
- Quick start (3-step onboarding)
- The 5 skills table
- The 4 agents overview
- Common workflows
- Troubleshooting quick reference

**Use when:** You're new to the plugin or need general help

---

### Discovery & Learning

#### 🔍 `/kengotg-show-skills`
**List all 5 production-ready skills with descriptions and use cases.**

- 5 skills: ixnetwork-to-keng-converter, otg-config-generator, snappi-script-generator, ixia-c-deployment, keng-licensing
- What each skill does
- When to use each skill
- Input/output formats
- Quick start examples

**Use when:** You want to know what capabilities are available

---

#### 🤖 `/kengotg-show-agents`
**List all 5 intelligent subagents and their responsibilities.**

- 4 agents: ixia-c-deployment-agent, otg-config-generator-agent, snappi-script-generator-agent, keng-licensing-agent
- Role and responsibilities for each
- When to invoke each agent
- Orchestration patterns (sequential, parallel)
- Decision tree for agent dispatch

**Use when:** You want to understand how agents work and orchestration

---

#### 📐 `/kengotg-show-architecture`
**Display orchestration architecture and workflow diagrams.**

- System architecture diagram (orchestrator → intent → agents)
- Greenfield pipeline (deploy → config → script)
- Parallel execution pattern (licensing + infrastructure in parallel)
- Existing infrastructure workflow
- Licensing-only pattern
- Data flow and port alignment
- Validation and error recovery

**Use when:** You want visual understanding of system design and data flow

---

#### 📖 `/kengotg-examples`
**Workflow examples by use case (8 real-world scenarios).**

- Example 1: Greenfield BGP test (deploy + config + script)
- Example 2: Quick license check
- Example 3: IxNetwork migration
- Example 4: Existing infrastructure + custom test
- Example 5: Multi-protocol complex test
- Example 6: Parallel execution (licensing + deployment)
- Example 7: Performance baseline test
- Example 8: Minimal validation test
- Decision tree for matching your use case

**Use when:** You need to see how to use the plugin for your specific scenario

---

#### 📝 `/kengotg-skill-help`
**Detailed skill documentation and quick reference.**

Complete documentation for each of the 5 skills:
1. ixnetwork-to-keng-converter — conversion + feasibility analysis
2. otg-config-generator — intent → OTG JSON config
3. snappi-script-generator — OTG config → executable Python
4. ixia-c-deployment — Docker Compose and Containerlab provisioning
5. keng-licensing — cost calculation + tier recommendations

- What each skill does
- Supported protocols and features
- Unsupported features and limitations
- Input/output formats
- Complete examples

**Use when:** You need in-depth documentation on a specific skill

---

#### 🧪 `/kengotg-eval-agents`
**Agent evaluation framework and test cases (20 questions total).**

- Framework overview (5 evaluation scenarios per agent)
- Evaluation scope: happy path, edge cases, complexity, error handling, real-world
- 5 evaluations per agent with success criteria
- How to run evaluations manually
- Scoring system and quality metrics

**Use when:** You want to understand agent quality or run evaluations

---

## ⚡ Section A: Skill Shortcuts (5 Commands)

Quick-access commands for rapid skill invocation with sensible defaults.

#### 🎯 `/kengotg-otg-gen`
**Quick OTG config generation from natural language.**

Wrapper around otg-config-generator skill with helpful prompts.

**Use when:** You want to generate an OTG config quickly without full customization

---

#### 🐍 `/kengotg-snappi-script`
**Quick Snappi test script generation from OTG config.**

Wrapper around snappi-script-generator skill with defaults.

**Use when:** You want to generate a test script quickly from an existing OTG config

---

#### 🚀 `/kengotg-deploy-ixia`
**Quick Ixia-c deployment (Docker Compose or Containerlab).**

Wrapper around ixia-c-deployment skill with topology selection.

**Use when:** You want to deploy infrastructure quickly without detailed customization

---

#### 💰 `/kengotg-licensing`
**Quick licensing check and cost estimation.**

Wrapper around keng-licensing skill with common scenarios.

**Use when:** You need a fast licensing recommendation or cost estimate

---

#### 🔄 `/kengotg-migrate-ix`
**Quick IxNetwork migration to OTG/KENG format.**

Wrapper around ixnetwork-to-keng-converter skill with validation.

**Use when:** You want to quickly convert an IxNetwork config to OTG

---

#### 🧹 `/kengotg-cleanup`
**Clean up all Ixia-c containers, veth pairs, and Containerlab topologies.**

Remove all infrastructure artifacts and return to clean state.

**Use when:** You want to reset the environment between test sessions

---

## 🔗 Section B: Workflow Commands (4 Commands)

End-to-end orchestration commands that chain multiple agents/skills together.

#### 🏗️ `/kengotg-create-test`
**Full test creation pipeline: deploy → config → script.**

Complete greenfield workflow:
1. Deploy Ixia-c infrastructure (Docker or Containerlab)
2. Generate OTG config from your test intent
3. Generate Snappi test script
4. Execute and validate

**Use when:** You have a blank slate and want to create a complete test from start to finish

---

#### 🚄 `/kengotg-quick-bgp-test`
**BGP test with optimized defaults (one-liner).**

Fast-track BGP testing:
- Pre-optimized settings for BGP convergence tests
- Minimal input (just port count and ASNs)
- Instant deployment, config, and script
- Ready to run immediately

**Use when:** You want a quick BGP test without configuration overhead

---

#### 📦 `/kengotg-migrate-and-run`
**IxNetwork migration + execution workflow.**

Complete migration pipeline:
1. Analyze IxNetwork config feasibility
2. Convert to OTG format
3. Deploy matching infrastructure
4. Generate and execute test script
5. Return results

**Use when:** You're migrating from IxNetwork and want end-to-end execution

---

#### 📊 `/kengotg-check-licensing`
**Complete licensing evaluation workflow.**

Full licensing assessment:
1. Gather test parameters (port counts, protocol complexity)
2. Calculate licensing costs
3. Compare tier options
4. Show ROI and recommendations
5. Generate cost report

**Use when:** You need licensing guidance before committing to a test campaign

---

## Quick Reference Table

| Command | Type | Purpose | Section |
|---------|------|---------|---------|
| `/kengotg-keng-help` | Help | Plugin overview | C |
| `/kengotg-show-skills` | Discovery | List 5 skills | C |
| `/kengotg-show-agents` | Discovery | List 4 agents | C |
| `/kengotg-show-architecture` | Discovery | Architecture diagrams | C |
| `/kengotg-examples` | Learning | Workflow examples | C |
| `/kengotg-skill-help` | Reference | Detailed skill docs | C |
| `/kengotg-eval-agents` | Reference | Evaluation framework | C |
| `/kengotg-otg-gen` | Shortcut | Quick OTG config | A |
| `/kengotg-snappi-script` | Shortcut | Quick script gen | A |
| `/kengotg-deploy-ixia` | Shortcut | Quick deployment | A |
| `/kengotg-licensing` | Shortcut | Quick license check | A |
| `/kengotg-migrate-ix` | Shortcut | Quick migration | A |
| `/kengotg-cleanup` | Shortcut | Environment reset | A |
| `/kengotg-create-test` | Workflow | Full pipeline | B |
| `/kengotg-quick-bgp-test` | Workflow | BGP shortcut | B |
| `/kengotg-migrate-and-run` | Workflow | Migration + execute | B |
| `/kengotg-check-licensing` | Workflow | Licensing evaluation | B |

---

## Command Selection Guide

### I'm new to the plugin
→ Start with `/kengotg-keng-help` → `/kengotg-examples` → Choose a workflow

### I want to see all skills
→ `/kengotg-show-skills`

### I want to understand orchestration
→ `/kengotg-show-agents` → `/kengotg-show-architecture`

### I want to create a test (greenfield)
→ `/kengotg-create-test`

### I need BGP testing quickly
→ `/kengotg-quick-bgp-test`

### I'm migrating from IxNetwork
→ `/kengotg-migrate-and-run`

### I need licensing guidance
→ `/kengotg-check-licensing`

### I want detailed skill documentation
→ `/kengotg-skill-help`

### I want to evaluate agent quality
→ `/kengotg-eval-agents`

### I need to clean up infrastructure
→ `/kengotg-cleanup`

---

## Command Organization

**Section C (Help & Discovery):** Educational tier — learn, explore, understand
- Onboarding for new users
- Deep documentation
- Discovery and learning resources

**Section A (Shortcuts):** Efficiency tier — quick access with defaults
- One-command skill invocation
- Pre-configured for common scenarios
- Fast execution

**Section B (Workflows):** Orchestration tier — end-to-end pipelines
- Multiple agents chained together
- Complete from start to finish
- Maximum automation

---

## Next Steps

1. **New user?** → `/kengotg-keng-help`
2. **Exploring skills?** → `/kengotg-show-skills`
3. **Need examples?** → `/kengotg-examples`
4. **Ready to build?** → `/kengotg-create-test` or `/kengotg-quick-bgp-test`
5. **Migrating from IxNetwork?** → `/kengotg-migrate-and-run`
