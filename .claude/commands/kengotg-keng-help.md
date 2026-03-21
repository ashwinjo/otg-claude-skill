---
name: kengotg-keng-help
description: Plugin overview, quick start guide, and help
disable-model-invocation: false
allowed-tools: []
---

# KENG OTG Traffic Testing Pipeline — Plugin Help

Welcome to the **KENG OTG (Open Traffic Generator)** traffic testing plugin for Claude Code.

This plugin automates the complete workflow for creating, deploying, and executing network traffic tests using Open Traffic Generator (KENG/Ixia-c).

---

## What is KENG?

**KENG** (aka **Open Traffic Generator** / **OTG**) is a vendor-neutral, standardized API for traffic generation and network testing. This plugin provides:

- **IxNetwork Migration:** Convert IxNetwork configs to KENG/OTG format
- **Test Automation:** Generate production-ready test scripts from test descriptions
- **Infrastructure Deployment:** Deploy Ixia-c (containerized traffic generator) with Docker or Containerlab
- **Licensing Guidance:** Cost estimation and license tier recommendations
- **Orchestration:** Intelligent agent-based workflow coordination

---

## Quick Start (3 Steps)

### 1. Check Available Skills
```
/show-skills
```
Lists all 5 production-ready skills and their use cases.

### 2. See Orchestration Architecture
```
/show-agents
/show-architecture
```
Understand how agents coordinate to build your test setup.

### 3. Choose Your Path

**Path A: Greenfield Test Setup**
```
@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose for BGP testing

@otg-config-generator-agent Create BGP test: 2 ports, AS 65001/65002, 1000 pps bidirectional

@snappi-script-generator-agent Generate Snappi test script
```

**Path B: Existing Infrastructure**
```
@otg-config-generator-agent Create BGP test: I have Ixia-c at localhost:8443

@snappi-script-generator-agent Generate Snappi test script
```

**Path C: Licensing Question**
```
@keng-licensing-agent What license for 4×100GE ports + 8 BGP sessions?
```

---

## The 5 Skills

| Skill | Purpose | Use When |
|-------|---------|----------|
| **ixnetwork-to-keng-converter** | IxNetwork → OTG | Migrating from IxNetwork |
| **otg-config-generator** | Natural language → OTG config | Creating test configs |
| **snappi-script-generator** | OTG config → Python script | Generating executable tests |
| **ixia-c-deployment** | Infrastructure provisioner | Setting up Ixia-c |
| **keng-licensing** | Cost & licensing advisor | Planning budget/licenses |

Type `/kengotg-show-skills` for detailed descriptions and quick start examples.

---

## The 4 Intelligent Agents

Agents orchestrate multi-step workflows:

| Agent | Role | Invoke |
|-------|------|--------|
| 🔵 **ixia-c-deployment-agent** | Infrastructure deployer | `@ixia-c-deployment-agent Deploy...` |
| 🟢 **otg-config-generator-agent** | Intent → Config translator | `@otg-config-generator-agent Create...` |
| 🟣 **snappi-script-generator-agent** | Config → Script executor | `@snappi-script-generator-agent Generate...` |
| 🟠 **keng-licensing-agent** | Licensing & cost advisor | `@keng-licensing-agent What license...?` |

Type `/kengotg-show-agents` for detailed responsibilities and invocation patterns.

---

## Common Workflows

### 1. Complete Greenfield Test (Deploy + Config + Script)
```
@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose

@otg-config-generator-agent Create BGP test: 2 ports, AS 65001/65002, bidirectional 1000 pps

@snappi-script-generator-agent Generate test script from the OTG config
```
**Outputs:** docker-compose.yml, otg_config.json, test_bgp_convergence.py (ready to run)

### 2. Quick License Check
```
@keng-licensing-agent What license for 4×100GE + 8 BGP sessions?
```
**Output:** Cost estimate + tier recommendation

### 3. IxNetwork Migration
```
@ixnetwork-to-keng-converter [paste IxNetwork config]
```
**Output:** OTG config + migration report

### 4. Config-Only (Use Existing Infrastructure)
```
@otg-config-generator-agent Create BGP test with Ixia-c at localhost:8443

@snappi-script-generator-agent Generate test script
```
**Output:** otg_config.json, test_bgp.py

Type `/kengotg-examples` to see more workflow patterns.

---

## Key Concepts

### Port Mapping & Alignment
Critical: Deployment outputs port locations that MUST be injected into configs.
```
Deploy → {"te1": "veth-a", "te2": "veth-z"}
           ↓
Config → Uses veth-a, veth-z for port locations
           ↓
Script → Connects to correct ports
```

### Standalone Scripts
All generated Snappi scripts are **self-contained**:
- ✓ No external config files
- ✓ All infrastructure details embedded
- ✓ Ready to run: `python test_xxx.py`
- ✓ Only dependency: `pip install snappi`

### OTG Schema Validation
All generated OTG configs validate against the OpenAPI schema (openapi.yaml).

---

## Discovery Commands

Explore the plugin:

```
/show-skills          # List 5 skills + use cases
/show-agents          # List 4 agents + responsibilities
/show-architecture    # Workflow diagrams & patterns
/examples             # Workflow examples by use case
/eval-agents          # Agent evaluation framework
/skill-help           # Detailed skill documentation
/keng-help            # This help (plugin overview)
```

---

## Typical Session Flow

```
1. User: "I need a BGP convergence test"
   ↓
2. Claude: Classify intent → Greenfield (need deploy + config + script)
   ↓
3. Dispatch agents sequentially:
   - 🔵 Deploy Ixia-c
   - 🟢 Generate OTG config (with port mapping)
   - 🟣 Generate Snappi script (with embedded config)
   ↓
4. Outputs: docker-compose.yml, otg_config.json, test_bgp.py
   ↓
5. User: "Run the test"
   ↓
6. Snappi script executes, generates JSON report
```

---

## Troubleshooting

### "Ports don't align"
Check that deployment port mapping matches config port locations.
Use `/kengotg-show-architecture` to understand data flow.

### "Script won't run"
Verify Python syntax: `python test_xxx.py --help`
Check Snappi SDK installed: `pip install snappi`

### "What license tier?"
Use `@keng-licensing-agent` to get recommendations based on your test scale.

### "How do I migrate IxNetwork?"
Use `@ixnetwork-to-keng-converter` to check feasibility and see conversion.

### "Script times out connecting"
Verify controller URL and port in script.
Check controller health: `curl -k https://localhost:8443/config`

---

## Next Steps

1. **Start small:** Try `/kengotg-examples` to see workflow patterns
2. **Choose your path:** Greenfield, existing infra, or licensing check
3. **Invoke agents:** Use `@agent-name` syntax
4. **Review outputs:** Check generated configs and scripts
5. **Run tests:** Execute Snappi scripts and collect metrics

---

## Documentation

```bash
# Project overview
cat README.md

# Detailed orchestration patterns
cat AGENT_ORCHESTRATION_PLAN.md

# Skill documentation
cat .claude/skills/INDEX.md
cat .claude/skills/*/SKILL.md

# Agent specifications
cat .claude/agents/README.md
cat .claude/agents/*-agent.md

# Evaluation framework
cat .claude/agents/eval-sets/README.md
cat .claude/agents/eval-sets/*.json
```

---

## Support

- **Commands:** Type `/kengotg-keng-help` for this help
- **Skills:** Type `/kengotg-show-skills` to list all 5 skills
- **Agents:** Type `/kengotg-show-agents` to understand orchestration
- **Examples:** Type `/kengotg-examples` for workflow patterns
- **Architecture:** Type `/kengotg-show-architecture` for diagrams

---

## About

**KENG OTG Traffic Testing Pipeline**
- 5 production-ready skills
- 4 intelligent subagents
- 20 evaluation questions
- Complete orchestration framework
- Docker & Containerlab support
- BGP, OSPF, LACP, LLDP protocols
- Snappi SDK integration
- OTG schema validation
- Comprehensive documentation

**Built for:** Network automation engineers, test automation, network DevOps, infrastructure teams.

**Supported Topologies:**
- BGP convergence testing
- Protocol failover simulation
- LAG and LACP testing
- Multi-protocol networks
- IxNetwork migrations

**License:** Check with Solutions Engineer for KENG licensing options and costs.
