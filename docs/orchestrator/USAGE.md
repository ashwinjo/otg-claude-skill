# OTG Orchestrator - User Guide

The OTG Orchestrator is the top-level coordination engine that orchestrates multi-agent test execution workflows. It understands your intent, dispatches to the right sub-agents, manages execution state, handles failures, and produces comprehensive artifacts.

## Quick Start

### Basic Invocation

```python
from skills.otg_orchestrator.skill_handler import invoke_skill

result = invoke_skill(
    user_request="Generate a BGP deployment with IxNetwork scripts and deploy to AWS",
    interactive=True,
    artifacts_dir="/tmp/my_test_run"
)

if result["success"]:
    print(f"Success! Artifacts at: {result['artifacts_dir']}")
else:
    print(f"Failed: {result['error']}")
```

### CLI Usage

```bash
# Interactive mode - wait for approvals at each checkpoint
python3 -m skills.otg_orchestrator.skill_handler \
    --request "Deploy Juniper Contrail with eBGP" \
    --interactive

# Batch mode - auto-proceed through all checkpoints
python3 -m skills.otg_orchestrator.skill_handler \
    --request "Generate SR Linux config only" \
    --no-interactive \
    --artifacts-dir /tmp/batch_run
```

## Use Cases

### Use Case 1: Full Greenfield Deployment

**Scenario:** You need a complete test topology with configuration, test scripts, infrastructure deployment, and licensing.

**Request:**
```
"I need a Juniper Contrail setup with eBGP across 3 regions,
test it with IxNetwork, deploy to AWS, and set up enterprise licensing"
```

**Orchestrator Flow:**
```
1. Intent Intake
   └─ Classify: FULL_GREENFIELD
   └─ Ask: device type? → Juniper
   └─ Ask: protocols? → eBGP
   └─ Ask: scale? → 3 regions
   └─ Ask: infrastructure? → AWS
   └─ Ask: license tier? → Enterprise

2. Dispatch Queue
   ├─ Config Generator
   ├─ IxNetwork Script Generator
   ├─ Deployment Agent
   └─ Licensing Agent

3. Execute (with checkpoints)
   Checkpoint 1: Config Generator
   ├─ Generates: config.yaml
   └─ User: [APPROVE] → Continue

   Checkpoint 2: Script Generator
   ├─ Generates: test_bgp_convergence.py, test_link_failure.py
   └─ User: [APPROVE] → Continue

   Checkpoint 3: Deployment
   ├─ Provisions: AWS infrastructure
   ├─ Deploys: configuration
   └─ User: [APPROVE] → Continue

   Checkpoint 4: Licensing
   ├─ Validates: existing licenses
   ├─ Applies: enterprise tier
   └─ User: [APPROVE] → Continue

4. Artifacts
   ├─ config.yaml
   ├─ test_bgp_convergence.py
   ├─ test_link_failure.py
   ├─ deployment_manifest.json
   ├─ license_report.md
   └─ MANIFEST.json (execution flow)
```

**Expected Duration:** 15-20 minutes

**Key Decisions:**
- Review config for correctness before Script Generator runs
- Review test scripts for coverage before Deployment
- Review deployment details before Licensing

---

### Use Case 2: Configuration + Scripts Only

**Scenario:** You want generated configs and test scripts, but will deploy manually.

**Request:**
```
"Create an SR Linux configuration for a 5-stage pipeline with MPLS,
and generate comprehensive test scripts for convergence validation"
```

**Orchestrator Flow:**
```
1. Intent Intake
   └─ Classify: CONFIG_AND_SCRIPT
   └─ Questions: device type, protocols, scale

2. Dispatch Queue
   ├─ Config Generator
   └─ IxNetwork Script Generator

3. Execute
   Checkpoint 1: Config Generator → [APPROVE]
   Checkpoint 2: Script Generator → [APPROVE]

4. Artifacts
   ├─ config.yaml
   ├─ test_mpls_convergence.py
   ├─ test_rsvp_failure.py
   └─ MANIFEST.json
```

**Expected Duration:** 5-8 minutes

**Next Steps:** Download artifacts, deploy manually using your deployment infrastructure

---

### Use Case 3: Deployment of Existing Configuration

**Scenario:** You have a previously generated config and want to deploy it.

**Request:**
```
"Deploy the SR Linux config from my last run to AWS with standard licensing"
```

**Orchestrator Flow:**
```
1. Intent Intake
   └─ Classify: DEPLOYMENT_ONLY
   └─ Ask: which previous run? → Select from recent runs

2. Dispatch Queue
   ├─ Deployment Agent
   └─ Licensing Agent

3. Execute
   Checkpoint 1: Deployment → [APPROVE]
   Checkpoint 2: Licensing → [APPROVE]

4. Artifacts
   ├─ deployment_manifest.json
   ├─ license_report.md
   └─ MANIFEST.json
```

**Expected Duration:** 10-15 minutes

---

### Use Case 4: Test Scripts Only

**Scenario:** You have a device configuration and just need test scripts.

**Request:**
```
"Generate comprehensive IxNetwork test scripts for BGP convergence,
link failure, and graceful restart scenarios"
```

**Orchestrator Flow:**
```
1. Intent Intake
   └─ Classify: SCRIPT_ONLY
   └─ Ask: target protocols? → BGP
   └─ Ask: what scenarios? → Convergence, link failure, graceful restart

2. Dispatch Queue
   └─ IxNetwork Script Generator

3. Execute
   Checkpoint 1: Script Generator → [APPROVE]

4. Artifacts
   ├─ test_bgp_convergence.py
   ├─ test_bgp_link_failure.py
   ├─ test_bgp_graceful_restart.py
   └─ MANIFEST.json
```

**Expected Duration:** 3-5 minutes

---

### Use Case 5: License Validation Only

**Scenario:** Check current license status and get tier recommendations.

**Request:**
```
"Validate my existing IxNetwork licenses and recommend the right tier
for a 3-region, 5-device BGP deployment"
```

**Orchestrator Flow:**
```
1. Intent Intake
   └─ Classify: LICENSING_ONLY
   └─ Ask: current setup details? → 3 regions, 5 devices, BGP

2. Dispatch Queue
   └─ Licensing Agent

3. Execute
   Checkpoint 1: Licensing Agent → [APPROVE]

4. Artifacts
   ├─ license_report.md
   ├─ tier_recommendations.json
   └─ MANIFEST.json
```

**Expected Duration:** 2-3 minutes

---

## Checkpoints & Approval Gates

The orchestrator pauses after each sub-agent completes a checkpoint. In interactive mode, you can:

### Approval Options

```
Checkpoint 3: Deployment Agent
Generated artifacts:
  - deployment_manifest.json (12 KB)
  - topology.png (visualization)

What would you like to do?
[A] APPROVE - Continue to next agent
[R] REVIEW  - Show full output
[S] SKIP    - Skip this agent (if optional)
[E] EDIT    - Modify intent for next agent
[X] ABORT   - Stop entire workflow

Your choice: A
```

### Batch Mode

In batch mode (`interactive=False`), all checkpoints automatically [APPROVE]:

```python
result = invoke_skill(
    user_request="...",
    interactive=False  # Auto-approve all checkpoints
)
```

This is useful for:
- CI/CD pipelines
- Scheduled test runs
- Automated regression testing
- Proof-of-concept demos

---

## Artifacts Directory

All output is saved to `artifacts/run-<timestamp>/` by default, or your specified `artifacts_dir`.

### Structure

```
artifacts/run-2025-03-19-152030/
├── MANIFEST.json              # Complete execution record
│   ├── metadata
│   │   ├─ start_time
│   │   ├─ end_time
│   │   ├─ total_duration_seconds
│   │   ├─ use_case
│   │   └─ status (completed/failed/aborted)
│   ├── execution_flow
│   │   ├─ agent: "config_generator"
│   │   │   ├─ start_time
│   │   │   ├─ duration_seconds
│   │   │   ├─ status: "success"
│   │   │   └─ outputs: [list of files]
│   │   ├─ agent: "script_generator"
│   │   ├─ agent: "deployment"
│   │   └─ agent: "licensing"
│   └── artifacts
│       └─ [list of all generated files]
│
├── SUMMARY.md                 # Human-readable overview
│   ├── Executive Summary
│   ├── Use Case
│   ├── Execution Flow
│   ├── Artifacts Generated
│   ├── Issues and Resolutions
│   └── Next Steps
│
├── config.yaml                # Device configuration (if generated)
├── test_bgp_convergence.py    # Test scripts (if generated)
├── test_link_failure.py
├── deployment_manifest.json   # Deployment record (if deployed)
├── license_report.md          # License status (if licensing run)
│
└── checkpoints/
    ├── checkpoint_1_config_generator.json
    ├── checkpoint_2_script_generator.json
    ├── checkpoint_3_deployment.json
    └── checkpoint_4_licensing.json
```

### Reusing Artifacts

Previous artifacts can be referenced in future runs:

```python
# First run: Generate config
result1 = invoke_skill(
    user_request="Generate SR Linux config for 5-stage pipeline with MPLS",
    artifacts_dir="/tmp/run1"
)

# Second run: Deploy the config from first run
result2 = invoke_skill(
    user_request="Deploy config from /tmp/run1 to AWS",
    artifacts_dir="/tmp/run2"
)
```

---

## Error Recovery

When an agent fails, the orchestrator classifies the error and offers recovery options.

### Error Categories

#### 1. Transient Errors (Auto-Retry)

**Examples:**
- Network timeout
- Connection refused (service restarting)
- Rate limit exceeded
- DNS resolution failure

**Behavior:**
```
Agent: Script Generator
Error: Connection timeout (transient)

Retrying (1/3)... ⏳
Retrying (2/3)... ⏳
Retrying (3/3)... ⏳
✓ Success on retry 2
```

**Configuration:**
```python
# Retry strategy (in recovery.py)
RETRY_CONFIG = {
    "max_retries": 3,
    "initial_backoff_seconds": 1,
    "max_backoff_seconds": 30,
    "exponential_base": 2.0
}
```

#### 2. Validation Errors (User Clarification)

**Examples:**
- Missing required field in intent
- Invalid configuration syntax
- Incompatible device/protocol combination

**Behavior:**
```
Agent: Config Generator
Error: MPLS requires LDP or RSVP protocol

Recovery Option 1: [C] CLARIFY
  └─ Re-answer: Which protocol for MPLS? LDP / RSVP

Recovery Option 2: [S] SKIP (if optional)
Recovery Option 3: [X] ABORT

Your choice: C
Q: Which protocol for MPLS - LDP or RSVP?
A: RSVP

Retrying with updated intent...
✓ Config generated with RSVP
```

#### 3. Terminal Errors (User Decision)

**Examples:**
- Agent version incompatible
- Infrastructure quota exceeded
- Unsupported deployment target
- License tier insufficient

**Behavior:**
```
Agent: Deployment
Error: AWS quota exceeded for t3.xlarge instances

Recovery options:
[1] SKIP - Deploy with t3.large instead
[2] CLARIFY - Change deployment parameters
[3] ABORT - Stop entire workflow

Your choice: 1

Deployment with t3.large...
✓ Successfully deployed
```

### Recovery in Logs

All recovery actions logged to `SUMMARY.md`:

```markdown
## Issues and Resolutions

### Checkpoint 2: Script Generator
**Error:** Connection timeout to IxNetwork REST API
**Classification:** Transient
**Action:** Automatic retry
**Result:** Success on retry 2 (after 4 seconds)

### Checkpoint 3: Deployment
**Error:** AWS quota for instances exceeded
**Classification:** Terminal
**Action:** User chose to SKIP (deploy with smaller instance type)
**Result:** Successfully deployed with t3.large
```

---

## Tips & Best Practices

### 1. Be Specific About Scale

❌ **Vague:**
```
"Create a network with BGP"
```

✓ **Specific:**
```
"Create a 3-region network with 5 devices per region using eBGP"
```

### 2. Mention Infrastructure Early

Infrastructure affects dispatcher decisions:

```
"Generate SR Linux config for containerlab"  # Prefers containerlab-compatible features
vs.
"Generate SR Linux config for AWS deployment"  # AWS-specific optimizations
```

### 3. Use Checkpoint Approvals

Review each artifact before the next agent runs:

```python
interactive=True  # ✓ Recommended for first runs
interactive=False # ✓ OK for proven workflows in CI/CD
```

### 4. Save and Archive Successful Runs

```bash
# Archive a successful run for future reference
mv artifacts/run-2025-03-19-152030 archived_runs/bgp_convergence_base

# Reuse in future requests
"Deploy configuration from archived_runs/bgp_convergence_base to AWS"
```

### 5. Check MANIFEST.json for Audit Trail

For compliance and debugging:

```bash
# View execution flow
cat artifacts/run-*/MANIFEST.json | jq '.execution_flow'

# Check error recovery actions
cat artifacts/run-*/SUMMARY.md | grep -A5 "Issues and Resolutions"
```

### 6. Use Batch Mode for Regression Testing

Once a workflow is proven:

```python
# Run weekly regression with auto-approval
result = invoke_skill(
    user_request="Run standard BGP convergence test suite",
    interactive=False,
    artifacts_dir=f"/tmp/regression_{datetime.now().isoformat()}"
)

# Archive results
if result["success"]:
    os.rename(result["artifacts_dir"], f"regression_passed_{timestamp}")
else:
    os.rename(result["artifacts_dir"], f"regression_failed_{timestamp}")
```

### 7. Progressive Validation

Start simple, then add complexity:

```python
# Step 1: Just config
result1 = invoke_skill("Generate SR Linux config for 3-device lab")

# Step 2: Add scripts
result2 = invoke_skill("Generate config + test scripts for 3-device lab with BGP")

# Step 3: Add deployment
result3 = invoke_skill("Generate, test, and deploy 3-device lab with BGP to containerlab")
```

### 8. Handle Long-Running Deployments

Deployment agent can take 10+ minutes:

```python
# Set longer timeout for large deployments
orchestrator = Orchestrator(
    transport=transport,
    artifacts_dir=artifacts_dir,
    deployment_timeout_seconds=1800  # 30 minutes
)
```

---

## Common Workflows

### Workflow 1: Development & Testing

```python
# 1. Generate config & scripts
result1 = invoke_skill(
    "Generate Juniper config and test scripts for BGP",
    interactive=True
)

# 2. Review artifacts
# - Check config.yaml for correctness
# - Check test scripts for coverage

# 3. Deploy to local lab
result2 = invoke_skill(
    f"Deploy config from {result1['artifacts_dir']} to containerlab",
    interactive=True
)

# 4. Run tests (external step)
# python test_bgp_convergence.py

# 5. If successful, archive
os.rename(result1["artifacts_dir"], "archived_runs/bgp_v1_approved")
```

### Workflow 2: Continuous Integration

```yaml
# In CI/CD pipeline
- name: Generate Test Configuration
  run: |
    python3 -m skills.otg_orchestrator.skill_handler \
      --request "Generate standard BGP test config" \
      --no-interactive

- name: Deploy to CI Lab
  run: |
    python3 -m skills.otg_orchestrator.skill_handler \
      --request "Deploy to CI containerlab" \
      --no-interactive

- name: Run Test Suite
  run: python3 test_bgp_convergence.py
```

### Workflow 3: Customer Demo

```python
# Pre-run in interactive mode
result = invoke_skill(
    "Deploy Juniper Contrail with BGP across 3 regions to AWS",
    interactive=True,
    artifacts_dir="/tmp/customer_demo"
)

# Review each checkpoint with customer
# Then run in presentation mode
```

---

## Troubleshooting

### Q: Orchestrator stuck at checkpoint?

**A:** In interactive mode, it's waiting for user input. Provide approval:
```python
# Or add timeout
orchestrator.checkpoint_timeout_seconds = 300  # 5 minutes
```

### Q: Agent failed but I want to retry?

**A:** Error classifier already retries transient errors automatically. For validation errors, respond to clarification prompt.

### Q: How do I skip an optional agent?

**A:** At checkpoint, choose [S] SKIP if agent is optional (e.g., Licensing).

### Q: Where are my artifacts?

**A:** Check `result["artifacts_dir"]` from return value. Also logged to stdout.

### Q: Can I resume an interrupted run?

**A:** Not yet. But checkpoints are saved for future resume capability. For now, create new run.

### Q: How do I debug agent invocation?

**A:** Check `MANIFEST.json` execution_flow. Each agent logs inputs/outputs/status.

---

## Next Steps

1. **Try a simple use case** - Start with "Generate SR Linux config only"
2. **Review artifacts** - Check generated files in artifacts directory
3. **Try interactive mode** - See checkpoint approval flow
4. **Try batch mode** - For CI/CD integration
5. **Archive successful runs** - Reuse as templates for future runs

For detailed technical documentation, see:
- `/docs/orchestrator/ARCHITECTURE.md` - System design
- `/src/orchestrator/` - Module reference
- `skills/otg-orchestrator/SKILL.md` - Skill manifest
