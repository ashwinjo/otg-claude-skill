---
name: skill-help
description: Detailed skill documentation and quick reference
disable-model-invocation: false
allowed-tools: []
---

# Skill Help — Detailed Documentation

In-depth documentation for each of the 5 production-ready skills.

---

## 1. ixnetwork-to-keng-converter

**Convert IxNetwork configurations to Open Traffic Generator (KENG/OTG) format.**

### What It Does
- Analyzes IxNetwork configs (Python RestPy or JSON format)
- Checks feasibility for KENG/OTG conversion
- Lists supported vs. unsupported features
- Generates equivalent OTG JSON config
- Produces detailed conversion report

### When to Use
- Migrating from IxNetwork to Ixia-c/KENG
- Evaluating KENG as IxNetwork replacement
- Converting existing tests for vendor-agnostic execution
- Need conversion report for decision-making

### Input Formats
```
✓ IxNetwork RestPy Python code
✓ IxNetwork JSON config
✓ Highlevel test description
```

### Output
```
✓ Feasibility report (0-100% convertible)
✓ OTG JSON config (for supported features)
✓ Conversion report (feature mapping table)
✓ Unsupported features list (with workarounds)
```

### Example Usage
```
@ixnetwork-to-keng-converter
[paste IxNetwork RestPy code]
```

### Supported Protocols
- ✓ BGP
- ✓ OSPF
- ✓ ISIS
- ✓ LACP
- ✓ LLDP
- ✓ IPv4/IPv6
- ✓ Traffic flows with custom packet definitions

### Unsupported Features
- ✗ Inline segment routing (may require workaround)
- ✗ Advanced SLA monitoring (basic metrics only)
- ✗ Some custom encapsulation types

### Output File
```
conversion_report.md    # Detailed mapping
converted_config.json   # OTG config
```

---

## 2. otg-config-generator

**Convert natural language test intent → Open Traffic Generator JSON configuration.**

### What It Does
- Parses English-language test descriptions
- Validates protocol and feature support
- Generates standards-compliant OTG JSON
- Injects port locations from infrastructure
- Validates against OTG schema (openapi.yaml)
- Aligns port definitions with device/flow setup

### When to Use
- Creating test scenarios from descriptions
- Building OTG configs without writing JSON
- Setting up multi-protocol tests
- Configuring traffic flows and assertions
- Need automated config generation

### Input
```
Natural language description:
"Create BGP convergence test with 2 ports, AS 65001 and AS 65002,
bidirectional 1000 pps traffic, 120 second duration,
assert BGP converges within 30 seconds"
```

### Output
```
otg_config.json                # OTG schema-compliant config
otg_config_summary.md          # Human-readable summary
port_alignment_report.md       # Port mapping verification
```

### Example Usage
```
@otg-config-generator-agent Create BGP test: 2 ports, AS 65001/65002, 1000 pps bidirectional
```

### Supported Test Types
- ✓ BGP convergence
- ✓ OSPF failover
- ✓ LACP/LAG testing
- ✓ ISIS convergence
- ✓ LLDP neighbor discovery
- ✓ Custom protocol sequences
- ✓ Traffic throughput measurement
- ✓ Failover simulation
- ✓ Multi-protocol interactions

### Key Features
- Injects port mapping from deployment phase
- Validates port count vs. intent
- Checks protocol compatibility
- Generates appropriate assertions
- Aligns with infrastructure constraints

### Port Alignment
**Critical:** Config must align with deployed infrastructure:
```
Deployment provides:
  {"te1": "veth-a", "te2": "veth-z", "controller": "localhost:8443"}

Config generator injects:
  "ports": [
    {"name": "te1", "location": "veth-a"},
    {"name": "te2", "location": "veth-z"}
  ]
```

---

## 3. snappi-script-generator

**Convert OTG configurations → standalone, executable Python Snappi test scripts.**

### What It Does
- Generates production-ready Python scripts
- Embeds OTG config in Python (no external files)
- Implements protocol setup and state polling
- Adds traffic control (start, stop, measure)
- Implements assertions and metrics collection
- Adds error handling and graceful cleanup
- Generates JSON reports with results

### When to Use
- Converting OTG configs to runnable tests
- Creating production test automation
- Need self-contained scripts
- Require error handling and reporting
- Want immediate execution without setup

### Input
```
otg_config.json           # OTG configuration
infrastructure.yaml       # Controller URL, port details
```

### Output
```
test_bgp_convergence.py   # Executable Python script (standalone)
execution_guide.md        # How to run, expected output
```

### Example Usage
```
@snappi-script-generator-agent Generate Snappi test script from bgp_config.json
```

### Generated Script Features
- ✓ Snappi SDK imports and setup
- ✓ Connection retry logic (configurable)
- ✓ OTG config embedded inline
- ✓ Protocol state polling
- ✓ Traffic start/stop control
- ✓ Metrics collection (throughput, latency, etc.)
- ✓ Assertion validation
- ✓ JSON report generation
- ✓ Full error handling
- ✓ Graceful resource cleanup

### Script Structure
```python
# 1. Imports & setup
import snappi
api = snappi.api()

# 2. OTG config embedded
config_dict = {...}  # Full OTG config inline
config = snappi.Config.deserialize(config_dict)

# 3. Protocol setup
api.set_config(config)
api.set_protocol_state(snappi.ProtocolState(...))

# 4. Traffic control
api.start_traffic()
time.sleep(test_duration)
api.stop_traffic()

# 5. Metrics collection
results = api.get_results()
assertions = validate_assertions(results, config)

# 6. Report generation
report = generate_json_report(results, assertions)
```

### Standalone Script Advantage
```
✓ python test_bgp.py        # Just run it
✗ No config file needed
✗ No setup.py required
✗ Only dependency: pip install snappi
```

### Error Handling
```python
# Connection errors
try:
    api.connect(controller_url, port)
except ConnectionError:
    # retry logic with exponential backoff
    pass

# Protocol timeout
try:
    poll_bgp_state(timeout=30)
except TimeoutError:
    # detailed error message
    pass

# Assertion failures
if not all_assertions_pass:
    # detailed failure report
    pass
```

---

## 4. ixia-c-deployment

**Deploy and configure Ixia-c (containerized traffic generator) infrastructure.**

### What It Does
- Analyzes deployment requirements
- Chooses Docker Compose vs. Containerlab
- Generates infrastructure manifests
- Manages container orchestration
- Configures networking (veth pairs, namespaces)
- Validates controller health and port connectivity
- Returns port mapping for downstream agents

### When to Use
- Setting up new Ixia-c infrastructure
- Choosing deployment topology
- Creating test environments
- Need port location mapping
- Infrastructure provisioning

### Topology Decisions
```
Docker Compose?
  ✓ Simple, single-host deployments
  ✓ Good for POCs and demos
  ✓ 2-10 ports typical
  ✓ Example: BGP convergence test

Containerlab?
  ✓ Complex multi-host topologies
  ✓ Network emulation (Linux containers)
  ✓ 20+ ports or distributed setup
  ✓ Example: Full network simulation
```

### Input
```
Deployment requirements:
  - Topology type (Docker/Containerlab)
  - Port count & speeds (10G, 25G, 100G)
  - Protocols (BGP, OSPF, LACP)
  - Host resource constraints
```

### Output
```
docker-compose.yml        # Docker Compose manifest
topo.clab.yml            # Containerlab manifest (if selected)
setup-ixia-c-bgp.sh      # Deployment automation script
port-mapping.json        # Port location mapping
deployment-guide.md      # Step-by-step instructions
```

### Port Mapping Format
```json
{
  "deployment_method": "docker-compose",
  "controller": {
    "url": "https://localhost:8443",
    "port": 8443,
    "status": "healthy"
  },
  "port_mapping": {
    "te1": "veth-a",
    "te2": "veth-z"
  },
  "traffic_engines": {
    "veth-a": {
      "container": "ixia-c-traffic-engine-a",
      "ip": "172.18.0.2",
      "data_port": 5555,
      "protocol_port": 50071
    }
  }
}
```

### Docker Compose Structure
```yaml
services:
  keng-controller:          # Control plane
  ixia-c-traffic-engine-a:  # Data plane (TE-A)
  ixia-c-traffic-engine-z:  # Data plane (TE-Z)
  keng-protocol-engine-a:   # Protocol stack (PE-A)
  keng-protocol-engine-z:   # Protocol stack (PE-Z)
```

### Validation Checks
- ✓ Controller reachable and healthy
- ✓ All traffic engines responsive
- ✓ Port connectivity verified
- ✓ Correct port mapping returned

### Example Usage
```
@ixia-c-deployment-agent Deploy Ixia-c with Docker Compose for BGP testing
```

---

## 5. keng-licensing

**Calculate licensing costs and recommend license tiers.**

### What It Does
- Calculates data plane costs (KENG-DPLU)
- Calculates control plane costs (KENG-CPLU)
- Recommends appropriate license tier
- Provides cost breakdown
- Includes Solutions Engineer disclaimers
- Compares tier options

### When to Use
- Planning test infrastructure budget
- Evaluating cost before purchase
- Choosing between license tiers
- Need licensing recommendations
- ROI analysis for KENG purchase

### Licensing Models

#### Data Plane Licensing (KENG-DPLU)
```
Cost based on port speeds:
  1×10GE    = 10 DPLU units
  1×25GE    = 25 DPLU units
  1×100GE   = 100 DPLU units

Example: 2×100GE + 2×10GE = 220 DPLU units
```

#### Control Plane Licensing (KENG-CPLU)
```
Cost based on protocol sessions:
  1×BGP session  = 1 CPLU unit
  1×OSPF session = 1 CPLU unit
  1×ISIS session = 1 CPLU unit
  LAGs, VLANs    = 0.5 CPLU each

Example: 4 BGP + 2 OSPF = 6 CPLU units
```

### License Tiers

#### Developer Tier
```
Capacity:   250 DPLU, 10 CPLU
Cost:       ~$X/month
Use case:   POCs, demos, small labs
Typical:    2-4 ports, minimal protocols
```

#### Team Tier
```
Capacity:   1000 DPLU, 50 CPLU
Cost:       ~$Y/month
Use case:   Production testing, multi-site
Typical:    8-20 ports, multiple protocols
```

#### System Tier
```
Capacity:   Unlimited
Cost:       ~$Z/month
Use case:   Enterprise, high-scale labs
Typical:    50+ ports, complex protocols
```

### Input
```
Test requirements:
  - Port count & speeds (e.g., 4×100GE)
  - Protocol count (e.g., 8 BGP sessions)
  - Use case (POC, production, etc.)
```

### Output
```
License recommendation + cost breakdown
Tier comparison (Developer, Team, System)
```

### Example Usage
```
@keng-licensing-agent What license for 4×100GE + 8 BGP sessions?
```

### Important Disclaimers
```
⚠️  Cost estimates are approximate
⚠️  Actual pricing may vary by region
⚠️  Verify with Solutions Engineer before purchase
⚠️  CPLU calculations assume standard protocols
⚠️  Complex features may require higher tier
```

---

## Skill Directory Structure

```
.claude/skills/
├── INDEX.md                              # Skill overview (start here)
├── ixnetwork-to-keng-converter/
│   ├── SKILL.md                          # Technical specification
│   ├── README.md                         # User guide
│   └── evals/evals.json                  # Test cases
├── otg-config-generator/
│   ├── SKILL.md
│   ├── README.md
│   └── evals/evals.json
├── snappi-script-generator/
│   ├── SKILL.md
│   ├── README.md
│   ├── evals/evals.json
│   └── references/                       # Examples & snippets
├── ixia-c-deployment/
│   ├── SKILL.md
│   ├── README.md
│   └── ref-*.md                          # Docker, Containerlab guides
└── keng-licensing/
    ├── SKILL.md
    └── evals.json
```

---

## Quick Reference

| Skill | Input | Output | Key Feature |
|-------|-------|--------|-------------|
| ixnetwork-to-keng-converter | IxNetwork config | OTG config + report | Migration analysis |
| otg-config-generator | English description | otg_config.json | Schema validation |
| snappi-script-generator | OTG config + YAML | test_xxx.py | Standalone scripts |
| ixia-c-deployment | Requirements | docker-compose.yml | Port mapping |
| keng-licensing | Port/protocol count | Cost estimate | Tier recommendation |

---

## Common Workflows

### Workflow 1: Start-to-Finish Test Creation
```
1. ixia-c-deployment      → Deploy infrastructure
2. otg-config-generator   → Create config (with port mapping)
3. snappi-script-generator → Generate script
4. Execute script        → Get results
```

### Workflow 2: IxNetwork Migration
```
1. ixnetwork-to-keng-converter   → Convert config + check feasibility
2. otg-config-generator (optional)   → Enhance/customize config
3. snappi-script-generator      → Generate test script
```

### Workflow 3: Existing Infrastructure
```
1. otg-config-generator   → Create config
2. snappi-script-generator → Generate script
3. Execute               → Get results
```

---

## See Also

- `/show-skills` — Quick skill list
- `/show-agents` — Agent orchestration
- `/show-architecture` — Workflow diagrams
- `/examples` — Real-world scenarios
- `/eval-agents` — Evaluation framework

For detailed technical specs:
```bash
cat .claude/skills/*/SKILL.md
```
