---
name: show-skills
description: List all 5 available skills with descriptions and use cases
disable-model-invocation: false
allowed-tools: []
---

# Show Skills

Display all 5 production-ready skills in the KENG OTG Traffic Testing Pipeline.

## Available Skills

### 1. 🔄 **ixnetwork-to-keng-converter**
Convert IxNetwork configurations to Open Traffic Generator (OTG/KENG) format.

**Use when:**
- Migrating from IxNetwork to Ixia-c/KENG
- Converting IxNetwork RestPy code to OTG JSON
- Checking IxNetwork config feasibility for KENG

**Input:** IxNetwork config (Python code or JSON)
**Output:** OTG JSON config + conversion report

**Quick start:**
```
/ixnetwork-to-keng-converter
```

---

### 2. 🎯 **otg-config-generator**
Convert natural language test intent → Open Traffic Generator JSON configuration.

**Use when:**
- Creating test scenarios from descriptions
- Generating OTG configs without writing JSON
- Setting up BGP, OSPF, LACP, LLDP, or other protocol tests
- Configuring traffic flows, ports, and assertions

**Input:** Test scenario description (plain English)
**Output:** `otg_config.json` + summary

**Quick start:**
```
/otg-config-generator
Create a BGP test with 2 ports, AS 65001 and 65002, 1000 pps bidirectional traffic
```

---

### 3. 🐍 **snappi-script-generator**
Convert OTG configurations → standalone, executable Python Snappi test scripts.

**Use when:**
- Generating runnable test scripts from OTG configs
- Creating production-ready test automation
- Need error handling, metrics, and assertions
- Want self-contained scripts (no external config files)

**Input:** OTG config JSON + infrastructure YAML
**Output:** `test_xxx.py` (executable)

**Quick start:**
```
/snappi-script-generator
```

---

### 4. 🚀 **ixia-c-deployment**
Deploy and configure Ixia-c (containerized traffic generator) infrastructure.

**Use when:**
- Setting up Ixia-c for testing
- Choosing between Docker Compose or Containerlab
- Creating veth pairs, configuring controllers
- Need port mappings for downstream agents

**Input:** Deployment topology (Docker, Containerlab)
**Output:** `docker-compose.yml` or `topo.clab.yml` + port mapping

**Quick start:**
```
/ixia-c-deployment
Deploy Ixia-c with Docker Compose for BGP testing
```

---

### 5. 💰 **keng-licensing**
Calculate licensing costs and recommend license tiers.

**Use when:**
- Planning test infrastructure costs
- Choosing between Developer/Team/System licenses
- Need cost estimates (DPLU/CPLU calculations)
- Evaluating ROI for KENG purchase

**Input:** Port count, protocol session count, use case
**Output:** License recommendation + cost breakdown

**Quick start:**
```
/keng-licensing
What license do I need for 4×100GE ports with 8 BGP sessions?
```

---

## Skill Directory

View skill documentation:
```bash
cat .claude/skills/INDEX.md                              # Skill overview
cat .claude/skills/ixnetwork-to-keng-converter/SKILL.md  # Detailed spec
cat .claude/skills/otg-config-generator/SKILL.md
cat .claude/skills/snappi-script-generator/SKILL.md
cat .claude/skills/ixia-c-deployment/SKILL.md
cat .claude/skills/keng-licensing/SKILL.md
```

## Next Steps

1. **Start with a use case:** BGP convergence test, LACP failover simulation, etc.
2. **Choose your path:**
   - Greenfield → Deploy + Configure + Generate Script
   - Existing infrastructure → Configure + Generate Script
   - Licensing check → Run licensing skill alone

3. **Use `/examples` to see workflow patterns**
4. **Use `/show-agents` to understand orchestration**

See `/keng-help` for plugin overview and `/show-architecture` for workflow diagrams.
