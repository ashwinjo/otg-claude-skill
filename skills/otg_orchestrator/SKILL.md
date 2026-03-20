# OTG Orchestrator Skill

Generate and execute comprehensive OTG test orchestration workflows across multiple sub-agents.

## Description

The OTG Orchestrator Skill orchestrates complex network test scenarios by:

1. **Intake** - Classifying your natural language request into a specific use case
2. **Dispatch** - Creating an execution plan with required sub-agents (Config Generator, Script Generator, Deployment, Licensing)
3. **Execute** - Running each agent in order with checkpoint approvals between steps
4. **Recover** - Handling transient failures with intelligent retry and recovery strategies

This is the top-level orchestration engine that coordinates all KENG sub-agents into a cohesive workflow.

## Usage

```
/orchestrator "Generate a Juniper Contrail deployment with BGP, then deploy it to AWS with licensing"
```

The orchestrator will:
1. Understand your intent (full greenfield scenario with infrastructure)
2. Dispatch to Config Generator → Script Generator → Deployment → Licensing
3. Wait for approval after each agent completes
4. Handle any errors with automatic recovery or user guidance
5. Generate comprehensive artifacts including execution manifest and summary

## Examples

### 1. Full Greenfield Deployment

**Request:**
```
"I need a complete Juniper Contrail deployment with eBGP between three regions,
deployed to AWS, with high-tier licensing"
```

**Expected Flow:**
- Config Generator: Creates Contrail configuration with multi-region BGP
- Script Generator: Creates IxNetwork test scripts for BGP validation
- Deployment Agent: Deploys to AWS with specified topology
- Licensing Agent: Applies high-tier licenses and validates
- **Artifacts:** `config.yaml`, `test_bgp_validation.py`, `deployment_manifest.json`, `license_report.md`

### 2. Configuration Only

**Request:**
```
"Just create a SR Linux configuration for a 5-stage pipeline with MPLS"
```

**Expected Flow:**
- Config Generator: Creates SR Linux config with MPLS
- **Artifacts:** `config.yaml`, verification report

### 3. Deploy Existing Configuration

**Request:**
```
"Deploy the existing SR Linux config from my last run to AWS"
```

**Expected Flow:**
- Deployment Agent: Reads stored config, deploys to AWS
- Licensing Agent: Applies standard license
- **Artifacts:** `deployment_manifest.json`, `license_validation.md`

### 4. Script Generation and Validation Only

**Request:**
```
"Create comprehensive test scripts for BGP convergence and link failure scenarios"
```

**Expected Flow:**
- Script Generator: Creates IxNetwork test scripts
- **Artifacts:** `test_bgp_convergence.py`, `test_link_failure.py`, `test_report.html`

### 5. License Validation Only

**Request:**
```
"Validate licenses for my existing deployment and provide tier recommendations"
```

**Expected Flow:**
- Licensing Agent: Validates current licenses, makes recommendations
- **Artifacts:** `license_report.md`, `tier_recommendations.json`

## How It Works

### Phase 1: Intent Intake
The orchestrator analyzes your natural language request and classifies it into one of these use cases:
- **Full Greenfield:** Config + Script + Deployment + Licensing
- **Config Only:** Just configuration generation
- **Config + Script:** Configuration and test scripts
- **Deployment Only:** Deploy existing config
- **Licensing Only:** License validation/setup

It then asks clarifying questions:
- Device type? (Juniper, Arista, SR Linux, etc.)
- Protocol focus? (BGP, OSPF, MPLS, etc.)
- Scale? (number of devices, links, etc.)
- Infrastructure? (On-prem, AWS, GCP, Azure, Containerlab)
- License tier? (Free, Standard, Premium, Enterprise)

### Phase 2: Dispatch
Based on your intent and answers, the orchestrator creates a dispatch queue with:
1. **Config Generator** (if config needed) - Creates device configurations
2. **Script Generator** (if scripts needed) - Creates IxNetwork test scripts
3. **Deployment Agent** (if deployment needed) - Deploys to infrastructure
4. **Licensing Agent** (if licensing needed) - Manages license activation

### Phase 3: Execute
For each agent in the queue:
1. The orchestrator invokes the agent with the current context
2. Captures output and saves checkpoint
3. Waits for user approval (interactive mode) or proceeds (batch mode)
4. On error: classifier determines if transient or terminal
5. On transient: automatic retry with backoff
6. On terminal: prompts user for guidance (skip, clarify, abort)

### Phase 4: Artifact Generation
After all agents complete:
1. **Execution Manifest:** Step-by-step record of what executed
2. **Summary Report:** High-level overview in markdown
3. **Artifacts Directory:** All generated files (configs, scripts, manifests)

## Artifacts

The orchestrator generates files in `artifacts/run-<timestamp>/`:

```
run-2025-03-19-152030/
├── MANIFEST.json          # Execution metadata and flow
├── SUMMARY.md             # High-level overview
├── config.yaml            # Device configuration (if generated)
├── test_scripts.py        # IxNetwork test scripts (if generated)
├── deployment_manifest.json # Deployment details (if deployed)
├── license_report.md      # License status and recommendations
└── checkpoints/
    ├── checkpoint_1.json  # Config generator output
    ├── checkpoint_2.json  # Script generator output
    ├── checkpoint_3.json  # Deployment output
    └── checkpoint_4.json  # Licensing output
```

## Error Recovery

The orchestrator handles three categories of errors:

### Transient (auto-retry)
- Network timeouts
- Connection refused (service restarting)
- Temporary DNS issues
- Rate limit exceeded

**Behavior:** Automatic retry with exponential backoff (1s, 2s, 4s, max 3 times)

### Validation (user guidance)
- Missing required fields in intent
- Invalid configuration syntax
- Incompatible device/protocol combination

**Behavior:** Prompts user to clarify intent, then retries

### Terminal (user decision)
- Agent version incompatibility
- Infrastructure quota exceeded
- Unsupported deployment target

**Behavior:** Offers options:
- Skip this agent (if optional)
- Clarify intent and try again
- Abort entire workflow

## Tips

**Best Practices:**

1. **Be specific about scale** - "5-stage pipeline" is better than "large network"
2. **Mention infrastructure early** - Helps dispatcher skip irrelevant agents
3. **Use checkpoint approvals** - Review output after each agent before proceeding
4. **Check artifacts directory** - All generated files saved for reuse
5. **Save successful runs** - Use `/archive` command to archive a successful run for future reference

**Advanced:**

- In batch mode (`interactive=false`), all approvals auto-proceed
- Recovery options are logged to `SUMMARY.md` for audit trails
- Checkpoints can be restored to resume interrupted runs
- All agent invocations captured in `MANIFEST.json` for debugging

## Related Skills

- **Config Generator** - Core device configuration generation
- **IxNetwork Script Generator** - Test automation script creation
- **Deployment Agent** - Infrastructure provisioning
- **Licensing Agent** - License management and validation
