# KENG OTG Traffic Testing Pipeline

**Complete network test automation toolkit** — Convert IxNetwork configs to OTG, generate test scripts, and automate traffic testing.

---

## Quick Start

### 5 Production-Ready Skills

#### 🔄 Skill #1: ixnetwork-to-keng-converter
**Migrate IxNetwork tests to vendor-neutral OTG format**
- Auto-detects RestPy code or JSON configs
- Performs feasibility analysis (supported/unsupported features)
- Generates OTG JSON + detailed conversion report
- Supports: BGP, Ethernet, IPv4, VLAN, Traffic flows
- **Use when:** Migrating from IxNetwork to KENG/ixia-c
- **Status:** ✅ Production-Ready

#### 🎯 Skill #2: otg-config-generator
**Generate OTG configurations from natural language**
- Converts test descriptions → vendor-neutral OTG JSON configs
- Supports: BGP, ISIS, LACP, LLDP, VLAN, multiple flows
- Validates schema compliance and constraints
- **Use when:** Creating OTG configs from scratch
- **Status:** ✅ Production-Ready

#### 🚀 Skill #3: snappi-script-generator
**Generate executable Snappi scripts from OTG configs**
- Converts OTG config + infrastructure YAML → standalone Python script
- Handles: API connection, protocol startup, metrics collection, assertions
- Interactive prompts (phase 1) → silent+JSON reports (phase 2)
- **Use when:** Need to execute tests on ixia-c/KENG
- **Status:** ✅ Production-Ready

#### 🚢 Skill #4: ixia-c-deployment
**Deploy and configure Ixia-c containerized traffic generator**
- Docker Compose: Multi-container setup (controller + traffic engines + protocol engine)
- Containerlab: Single-container deployment (ixia-c-one)
- Infrastructure provisioning and verification
- **Use when:** Setting up Ixia-c infrastructure before running tests
- **Status:** ✅ Production-Ready

#### 📋 Skill #5: keng-licensing
**Answer questions about OTG licensing costs and recommendations**
- Reference all license types: Developer, Team, System
- Calculate licensing costs for data plane (ports) and control plane (protocols)
- Recommend appropriate licenses based on test scenarios
- Never speculates or makes up information
- Always includes Solutions Engineer verification disclaimer
- **Use when:** Planning tests, understanding licensing costs, choosing license tier
- **Status:** ✅ Production-Ready

---

## Workflow Examples

### Example 1: Deploy Ixia-c → Generate & Execute OTG Test

```
Step 0: Deploy Ixia-c infrastructure
  User: "Deploy Ixia-c with Docker Compose"
  → /ixia-c-deployment (Method 1)
  → docker compose up -d
  → Infrastructure ready at localhost:8443

Step 1: Generate OTG config
  User: "Create BGP test with 2 ports, AS 101 and AS 102"
  → /otg-config-generator
  → bgp_config.json

Step 2: Generate test script
  User: "Generate Snappi script from bgp_config.json"
  → /snappi-script-generator
  → test_bgp.py

Step 3: Run test on Ixia-c
  python test_bgp.py
  → Test Results + JSON Report
```

### Example 2: Migrate IxNetwork → Execute on KENG

```
Step 0: Deploy Ixia-c with Containerlab
  User: "Deploy Ixia-c with Containerlab"
  → /ixia-c-deployment (Method 2)
  → sudo clab deploy -t topology.clab.yml
  → Ixia-c ready at 172.20.20.10:8443

Step 1: Convert IxNetwork config
  User: "Convert this IxNetwork RestPy BGP test"
  → /ixnetwork-to-keng-converter
  → otg_config.json + conversion_report.md

Step 2: Generate test script
  User: "Generate Snappi script from otg_config.json"
  → /snappi-script-generator
  → test_bgp.py

Step 3: Run test on Ixia-c
  python test_bgp.py
  → Test Results + JSON Report
```

### Example 3: Create OTG Config from Scratch → Execute


```
Step 1: Generate OTG config
  User: "Create BGP test with 2 ports, AS 101 and AS 102"
  → /otg-config-generator
  → bgp_config.json

Step 2: Generate test script
  User: "Generate Snappi script"
  → /snappi-script-generator
  → test_bgp.py

Step 3: Run test
  python test_bgp.py
```

### Example 3: Check IxNetwork → OTG Compatibility

```
User: "Can this IxNetwork OSPF test be converted to KENG?"
  → /ixnetwork-to-keng-converter
  → Feasibility report: "OSPF not supported in OTG MVP"
```

---

## Claude Commands (16 Total)

This plugin provides 16 Claude Commands organized in 3 tiers for different user needs.

### 🆘 Help & Discovery (Section C) — 7 commands
Perfect for learning the plugin:
- `/kengotg-keng-help` — Plugin overview & quick start
- `/kengotg-show-skills` — See all 5 skills
- `/kengotg-show-agents` — See all 4 intelligent agents
- `/kengotg-show-architecture` — Understand system design
- `/kengotg-examples` — 8 real-world workflow examples
- `/kengotg-skill-help` — Detailed skill documentation
- `/kengotg-eval-agents` — Agent evaluation framework (20 test scenarios)

**Start here:** `/kengotg-keng-help`

### ⚡ Quick Shortcuts (Section A) — 5 commands
Fast access to skills with sensible defaults:
- `/kengotg-otg-gen` — Quick OTG config generation
- `/kengotg-snappi-script` — Quick Snappi script generation
- `/kengotg-deploy-ixia` — Quick Ixia-c deployment
- `/kengotg-licensing` — Quick licensing check
- `/kengotg-migrate-ix` — Quick IxNetwork migration

**Use when:** Want quick defaults without customization

### 🔄 End-to-End Workflows (Section B) — 4 commands
Complete orchestration of multiple agents:
- `/kengotg-create-test` — Full pipeline (deploy→config→script)
- `/kengotg-quick-bgp-test` — BGP test shortcut with optimizations
- `/kengotg-migrate-and-run` — IxNetwork migration + execution
- `/kengotg-check-licensing` — Complete licensing evaluation workflow

**Use when:** Need full workflow, orchestrating multiple steps

---

## Project Structure

```
kengotg/
├── README.md                              This file (project overview)
├── AGENT_ORCHESTRATION_PLAN.md            Detailed orchestration patterns
├── openapi.yaml                           OTG schema reference (required by skills)
├── bgp_keng.json                          Example OTG config output
│
└── .claude/
    ├── commands/                          Claude Commands (16 total, ~150KB)
    │   ├── COMMANDS.md                    Command index & navigation
    │   ├── kengotg-*.md                   16 command files (organized by section)
    │   │
    │   ├─ Section C: Help & Discovery (7 commands)
    │   │  ├── kengotg-keng-help.md
    │   │  ├── kengotg-show-skills.md
    │   │  ├── kengotg-show-agents.md
    │   │  ├── kengotg-show-architecture.md
    │   │  ├── kengotg-examples.md
    │   │  ├── kengotg-skill-help.md
    │   │  └── kengotg-eval-agents.md
    │   │
    │   ├─ Section A: Skill Shortcuts (5 commands)
    │   │  ├── kengotg-otg-gen.md
    │   │  ├── kengotg-snappi-script.md
    │   │  ├── kengotg-deploy-ixia.md
    │   │  ├── kengotg-licensing.md
    │   │  └── kengotg-migrate-ix.md
    │   │
    │   └─ Section B: Workflows (4 commands)
    │      ├── kengotg-create-test.md
    │      ├── kengotg-quick-bgp-test.md
    │      ├── kengotg-migrate-and-run.md
    │      └── kengotg-check-licensing.md
    │
    ├── agents/                            Intelligent subagents (4 agents, 20 evals)
    │   ├── README.md                      Agent orchestration overview
    │   ├── ixia-c-deployment-agent.md     Infrastructure provisioner
    │   ├── otg-config-generator-agent.md  Intent → config translator
    │   ├── snappi-script-generator-agent.md Config → script executor
    │   ├── keng-licensing-agent.md        Licensing advisor
    │   └── eval-sets/                     Evaluation framework
    │       ├── README.md
    │       ├── ixia-c-deployment-agent-eval.json
    │       ├── otg-config-generator-agent-eval.json
    │       ├── snappi-script-generator-agent-eval.json
    │       └── keng-licensing-agent-eval.json
    │
    └── skills/                            Production-ready skills (5 skills, ~100KB)
        ├── INDEX.md                       Skill discovery guide (START HERE)
        │
        ├── ixnetwork-to-keng-converter/   Skill #1: IxNetwork → OTG
        │   ├── SKILL.md                   Technical reference
        │   ├── README.md                  User guide + troubleshooting
        │   ├── PRODUCTION_CHECKLIST.md
        │   └── evals/                     Test cases (4 scenarios)
        │
        ├── otg-config-generator/          Skill #2: Intent → OTG JSON
        │   ├── SKILL.md
        │   └── README.md
        │
        ├── snappi-script-generator/       Skill #3: OTG JSON → Python
        │   ├── SKILL.md
        │   ├── README.md
        │   └── references/                Protocol examples & snippets
        │
        ├── ixia-c-deployment/             Skill #4: Infrastructure provisioner
        │   ├── SKILL.md
        │   └── README.md
        │
        └── keng-licensing/                Skill #5: Licensing advisor
            ├── SKILL.md
            └── evals.json                 Test cases (8 scenarios)
```

---

## How to Use This Plugin

### Three Ways to Access Features

**Option 1: Claude Commands (Recommended for Most Users)**
```bash
# Help & learning
/kengotg-keng-help        ← Start here

# Quick tests
/kengotg-quick-bgp-test 2 ports   ← BGP with defaults

# Full workflows
/kengotg-create-test      ← Deploy + Config + Script
/kengotg-migrate-and-run  ← IxNetwork migration + execution
```

**Option 2: Skill Shortcuts (Quick with Sensible Defaults)**
```bash
# Fast, with good defaults
/kengotg-otg-gen          ← Generate config quickly
/kengotg-deploy-ixia      ← Deploy with defaults
```

**Option 3: Direct Skills & Agents (Full Control)**
```bash
# When you need complete customization
/ixnetwork-to-keng-converter    ← IxNetwork migration (detailed)
@ixia-c-deployment-agent       ← Orchestrate agents directly
```

**Choose commands for:**
- Learning the plugin
- Quick one-off tests
- Following recommended workflows

**Choose skills/agents for:**
- Advanced customization
- Complex scenarios
- Integration with other systems

---

## How to Use Each Skill

### 1️⃣ ixnetwork-to-keng-converter

**When:** You have an IxNetwork config you want to migrate

```bash
/ixnetwork-to-keng-converter

User: "Convert this IxNetwork RestPy code to OTG:

from ixnetwork_restpy.testplatform import TestPlatform
tp = TestPlatform('10.36.231.231', rest_port=443, userName='admin', password='admin')
...
"

Output:
  ✅ otg_config.json (ready to deploy)
  ✅ conversion_report.md (detailed analysis)
```

**Features:**
- Auto-detects Python/JSON formats
- Lists supported/unsupported features
- Provides workarounds for partial conversions
- Reports known differences
- Includes deployment instructions

---

### 2️⃣ otg-config-generator

**When:** You need to create an OTG config from a test scenario

```bash
/otg-config-generator

User: "Create a BGP test with 2 ports.
Port 1: AS 101, 10.0.0.1/24
Port 2: AS 102, 10.0.0.2/24
Bidirectional traffic at 1000 pps"

Output: Valid OTG JSON configuration
```

**Features:**
- Natural language to OTG JSON
- Supports all major protocols
- Full schema validation
- Constraint checking

---

### 3️⃣ snappi-script-generator

**When:** You have an OTG config and need to execute it

```bash
/snappi-script-generator

User: "Generate a Snappi test script from bgp_keng.json
Infrastructure: Ixia-c at 192.168.1.100:8443"

Output: test_bgp_keng.py (standalone, executable)
```

**Then execute:**
```bash
pip install snappi
python test_bgp_keng.py
```

**Features:**
- Standalone scripts (no external deps except snappi)
- Error handling & retry logic
- Metrics collection
- JSON report generation
- Interactive prompts or silent mode

---

### 4️⃣ ixia-c-deployment

**When:** You need to set up Ixia-c infrastructure before running tests

```bash
/ixia-c-deployment

User: "Deploy Ixia-c with Docker Compose for a lab test"

Output: docker-compose.yml + deployment instructions
```

**Then deploy:**
```bash
docker compose up -d
# Ixia-c available at https://localhost:8443
```

**Features:**
- Docker Compose (multi-container: controller + engines)
- Containerlab (single-container: ixia-c-one)
- Kubernetes Operator (for cloud deployments)
- Health checks & verification scripts
- Troubleshooting guides

---

### 5️⃣ keng-licensing

**When:** You need to understand OTG licensing costs or choose a license tier

```bash
/keng-licensing

User: "I need to run a test with 2x100GE ports and BGP+ISIS.
Should I use Team or System license and what will it cost?"

Output: License recommendation + cost breakdown + SE verification note
```

**Example questions:**
- "What's the difference between KENG-DPLU and KENG-CPLU?"
- "How many seats do I get with a Team license?"
- "Calculate cost for 3x10GE + 5 BGP sessions"
- "Which license should I choose for..."

**Features:**
- References all license types and allocations
- Calculates data plane costs (port speeds)
- Calculates control plane costs (protocol sessions)
- Recommends appropriate license tier
- Includes KENG-UNLIMITED-CP optimization guidance
- Always includes Solutions Engineer verification disclaimer
- **Never** makes up pricing or feature information

---

## Key Capabilities

| Capability | ixnetwork-to-keng | otg-config-gen | snappi-script-gen | ixia-c-deploy | keng-licensing |
|---|---|---|---|---|---|
| **BGP** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support | ✅ Cost calc |
| **Ethernet/IPv4** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support | N/A |
| **VLAN** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support | N/A |
| **ISIS** | ❌ Convert | ✅ Generate | ✅ Execute | ✅ Support | ✅ Cost calc |
| **LACP** | ❌ Convert | ✅ Generate | ✅ Execute | ✅ Support | ✅ Cost calc |
| **LLDP** | ❌ Convert | ✅ Generate | ✅ Execute | ✅ Support | N/A |
| **Traffic Flows** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support | N/A |
| **Feasibility Check** | ✅ Analysis | N/A | N/A | N/A | N/A |
| **Conversion Report** | ✅ Detailed | N/A | N/A | N/A | N/A |
| **Test Execution** | N/A | N/A | ✅ Full | N/A | N/A |
| **License Cost Calc** | N/A | N/A | N/A | N/A | ✅ Full |
| **License Recommendation** | N/A | N/A | N/A | N/A | ✅ Personalized |
| **Infrastructure Deploy** | N/A | N/A | N/A | ✅ Docker/Clab | N/A |
| **Health Verification** | N/A | N/A | N/A | ✅ API checks | N/A |
| **Troubleshooting** | N/A | N/A | N/A | ✅ Guides | N/A |

---

## Getting Started

### For IxNetwork Users

1. **Read:** `.claude/skills/INDEX.md` (skill discovery)
2. **Check License:** Use `/keng-licensing` to understand licensing requirements & costs
3. **Use:** `/ixnetwork-to-keng-converter` to convert your config
4. **Review:** `conversion_report.md` for compatibility
5. **Execute:** Use `/snappi-script-generator` to create test script

### For New OTG Users

1. **Read:** `.claude/skills/INDEX.md`
2. **Check License:** Use `/keng-licensing` to understand licensing options
3. **Use:** `/otg-config-generator` to create config from scratch
4. **Execute:** `/snappi-script-generator` to create test script
5. **Run:** `python test_xxx.py`

### For Test Automation

1. **Plan:** Use `/keng-licensing` to understand licensing costs & recommendations
2. **Generate:** OTG config (either converted or created)
3. **Create:** Snappi script with `/snappi-script-generator`
4. **Integrate:** `test_xxx.py` into your CI/CD pipeline
5. **Parse:** JSON reports for assertions/metrics

---

## Documentation

**Start here:**
- `.claude/skills/INDEX.md` — Skill overview & workflow examples
- `README.md` (this file) — Project overview

**For each skill:**
- `SKILL.md` — Technical deep-dive
- `README.md` — User guide + troubleshooting FAQ
- `evals/files/` — Example test cases

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ IxNetwork Config                                            │
│ (RestPy code or JSON)                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                    [CHOICE 1]
                         │
        ┌────────────────▼────────────────┐
        │ixnetwork-to-keng-converter      │
        │ - Feasibility check             │
        │ - Feature mapping               │
        │ - Conversion report             │
        └────────────────┬────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ OTG Configuration (JSON)                                    │
└─────────────┬───────────────────────────────────────────────┘
              │
        [CHOICE 2]
              │
    ┌─────────▼──────────┐
    │otg-config-generator│ (Alternative: create from scratch)
    └─────────┬──────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │ OTG Config                  │
    │ + Infrastructure YAML       │
    └─────────┬───────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │snappi-script-generator           │
    │ - API setup                      │
    │ - Protocol startup               │
    │ - Traffic control                │
    │ - Metrics collection             │
    │ - Error handling                 │
    └─────────┬──────────────────────────┘
              │
              ▼
    ┌──────────────────────────┐
    │Standalone Snappi Script  │
    │(test_xxx.py)             │
    └─────────┬────────────────┘
              │
              ▼
    python test_xxx.py
              │
              ▼
    ┌──────────────────────────┐
    │Test Results + JSON Report│
    └──────────────────────────┘
```

---

## Key Features

✅ **Vendor-neutral** — Works with any OTG-compliant traffic generator (ixia-c, KENG, etc.)
✅ **Standalone scripts** — No external dependencies besides snappi
✅ **Production-ready** — Error handling, retry logic, graceful cleanup
✅ **Fully documented** — Each skill has README, troubleshooting guide, test cases
✅ **Schema-validated** — All OTG configs validated against official schema
✅ **Interactive or automated** — Prompts for guidance, JSON reports for CI/CD

---

## For Your Organization

### Distribution

```bash
# Option 1: Direct copy
cp -r /Users/ashwin.joshi/kengotg /your/org/location/

# Option 2: Git submodule
git submodule add /path/to/kengotg .claude/skills/

# Option 3: Package for sharing
tar -czf kengotg-skills.tar.gz /path/to/kengotg
```

### Team Workflow

1. **Skill Discovery:** Start with `.claude/skills/INDEX.md`
2. **Conversion:** Use ixnetwork-to-keng-converter if migrating from IxNetwork
3. **Generation:** Use otg-config-generator for new tests or enhancements
4. **Execution:** Use snappi-script-generator to create automated test scripts
5. **CI/CD Integration:** Parse JSON reports from test runs

---

## Support

**Questions?**
- Each skill has a **README.md** with troubleshooting FAQ
- Review **SKILL.md** for technical details
- Check **evals/files/** for working examples
- See **.claude/skills/INDEX.md** for workflow guidance

---

## Status

| Skill | Version | Status | Last Updated |
|-------|---------|--------|---|
| ixnetwork-to-keng-converter | 1.0 | ✅ Production-Ready | 2026-03-17 |
| otg-config-generator | 1.0 | ✅ Production-Ready | 2026-03-17 |
| snappi-script-generator | 1.1 | ✅ Production-Ready | 2026-03-17 |
| ixia-c-deployment | 1.0 | ✅ Production-Ready | 2026-03-17 |
| keng-licensing | 1.0 | ✅ Production-Ready | 2026-03-18 |

---

**Complete OTG/KENG testing toolkit. Ready to use. Share with your organization.**
