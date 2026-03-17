# KENG OTG Traffic Testing Pipeline

**Complete network test automation toolkit** — Convert IxNetwork configs to OTG, generate test scripts, and automate traffic testing.

---

## Quick Start

### 3 Production-Ready Skills

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

## Project Structure

```
kengotg/
├── README.md                              This file
├── openapi.yaml                           OTG schema reference (required by skills)
├── bgp_keng.json                          Example OTG config output
│
└── .claude/skills/
    ├── INDEX.md                           ← Skill discovery guide (START HERE)
    │
    ├── ixnetwork-to-keng-converter/       Skill #1
    │   ├── SKILL.md                       Technical reference
    │   ├── README.md                      User guide + troubleshooting
    │   ├── PRODUCTION_CHECKLIST.md        QA & deployment guide
    │   └── evals/                         Test cases (4 scenarios)
    │
    ├── otg-config-generator/              Skill #2
    │   ├── SKILL.md
    │   └── README.md
    │
    ├── snappi-script-generator/           Skill #3
    │   ├── SKILL.md
    │   ├── README.md
    │   └── references/                    Protocol examples, assertions, GitHub snippets
    │
    └── ixia-c-deployment/                 Skill #4
        ├── SKILL.md                       Docker Compose, Containerlab, K8s options
        └── README.md                      (optional)
```

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

## Key Capabilities

| Capability | ixnetwork-to-keng-converter | otg-config-generator | snappi-script-generator | ixia-c-deployment |
|---|---|---|---|---|
| **BGP** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **Ethernet/IPv4** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **VLAN** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **ISIS** | ❌ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **LACP** | ❌ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **LLDP** | ❌ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **Traffic Flows** | ✅ Convert | ✅ Generate | ✅ Execute | ✅ Support |
| **Feasibility Check** | ✅ Analysis | N/A | N/A | N/A |
| **Conversion Report** | ✅ Detailed | N/A | N/A | N/A |
| **Test Execution** | N/A | N/A | ✅ Full automation | N/A |
| **Infrastructure Deploy** | N/A | N/A | N/A | ✅ Docker Compose / Containerlab |
| **Health Verification** | N/A | N/A | N/A | ✅ API checks |
| **Troubleshooting** | N/A | N/A | N/A | ✅ Guides |

---

## Getting Started

### For IxNetwork Users

1. **Read:** `.claude/skills/INDEX.md` (skill discovery)
2. **Use:** `/ixnetwork-to-keng-converter` to convert your config
3. **Review:** `conversion_report.md` for compatibility
4. **Execute:** Use `/snappi-script-generator` to create test script

### For New OTG Users

1. **Read:** `.claude/skills/INDEX.md`
2. **Use:** `/otg-config-generator` to create config from scratch
3. **Execute:** `/snappi-script-generator` to create test script
4. **Run:** `python test_xxx.py`

### For Test Automation

1. **Generate:** OTG config (either converted or created)
2. **Create:** Snappi script with `/snappi-script-generator`
3. **Integrate:** `test_xxx.py` into your CI/CD pipeline
4. **Parse:** JSON reports for assertions/metrics

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

---

**Complete OTG/KENG testing toolkit. Ready to use. Share with your organization.**
