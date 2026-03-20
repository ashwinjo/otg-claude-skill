# OTG Orchestrator: Robust Execution Design

**Date:** 2026-03-19
**Status:** Design Review
**Scope:** Claude Code orchestrator → future Anthropic SDK migration

---

## Executive Summary

This design establishes a **hybrid orchestrator** that validates user intent upfront, executes sub-agents with intelligent checkpointing (sequential for dependent agents, parallel for independent ones), and collects structured artifacts throughout execution. The orchestrator is robust (adaptive retry, smart recovery), auditable (complete artifact trail), and reusable (templates and patterns for future runs).

The orchestrator bridges Claude Code (immediate) and Anthropic SDK (future), ensuring architecture is platform-agnostic. A transport adapter layer abstracts platform differences, allowing identical orchestration logic to run on both platforms.

---

## Architecture Overview

```
User Intent
    ↓
┌─────────────────────────────────────┐
│  Phase 1: Intent Intake & Validation│  (Interactive)
│  - Ask clarifying questions         │
│  - Normalize intent                 │
│  - Validate against capabilities    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Phase 2: Dispatch with Checkpoints │  (Sequential + Auto)
│  - Invoke sub-agent 1               │
│  - Save checkpoint                  │
│  - Ask user for approval            │
│  - Proceed or edit                  │
│  - (Repeat for each sub-agent)      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Phase 3: Error Recovery            │  (Smart Fallback)
│  - Transient errors → retry         │
│  - Validation errors → clarify      │
│  - State mismatches → offer recovery│
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Phase 4: Artifact Collection       │  (Always)
│  - Structured manifest (JSON)       │
│  - Human summary (Markdown)         │
│  - Reusable templates               │
└─────────────────────────────────────┘
    ↓
Outputs + Structured Artifacts
```

---

## Design Section 1: Intent Intake & Validation

### Purpose
Convert raw user input into a normalized, validated intent object before any sub-agent is invoked.

### Flow
1. **Classify Intent:** Determine use case (full greenfield, config-only, deployment-only, script-only, licensing-only)
2. **Ask Clarifying Questions:** One at a time, fill in missing critical parameters
3. **Normalize:** Build standardized Intent object with all required fields
4. **Validate:** Check intent against sub-agent capabilities
5. **Persist:** Save intent as `intent_<timestamp>.json`

### Intent Schema
```json
{
  "user_request": "Create BGP test with 2 ports, deploy with Docker, get script + license",
  "use_case": "full_greenfield",

  "deployment": {
    "method": "docker_compose",
    "controller_url": "localhost:8443",
    "ports": [
      {"name": "te1", "speed": "100GE"},
      {"name": "te2", "speed": "100GE"}
    ]
  },

  "test_scenario": {
    "protocols": ["bgp"],
    "port_count": 2,
    "sessions": {"bgp": 4},
    "traffic_rate": "1000 pps"
  },

  "licensing": {
    "tier": "team",
    "estimate_required": true
  },

  "flags": {
    "ask_at_checkpoints": true,
    "auto_retry": true,
    "max_wait_time_minutes": 30
  }
}
```

### Clarifying Questions Template
```
Use Case Detection Questions:
1. Do you want to deploy Ixia-c, or use existing? (Deploy/Existing/Skip)
2. If deploying: Docker Compose or Containerlab? (Docker/Containerlab)
3. What test protocols? (BGP/ISIS/LACP/LLDP/other)
4. How many ports? (1/2/4/8+)
5. Port speeds? (1GE/10GE/25GE/40GE/100GE)
6. License tier? (Developer/Team/System)
```

### Why This Approach
- **All critical decisions upfront** → fewer surprises during execution
- **Validates against capabilities** → fail fast on impossible requests
- **Intent becomes a template** → reusable for future similar runs
- **Clear audit trail** → what user asked for is always recorded

---

## Design Section 2: State Machine & Orchestration

### Purpose
Manage execution flow across sub-agents with clear state transitions and checkpoints.

### Conditional Dispatch Model

The orchestrator determines which sub-agents to invoke based on the validated `use_case` field in the intent:

**Use Case Dispatch Paths** (from AGENT_ORCHESTRATION_PLAN.md):

```
Full Greenfield (full_greenfield):
  ┌─────────────────────┐
  │ 🔵 ixia-c-deploy    │ (parallel group A)
  └──────────┬──────────┘
             │
  ┌──────────────────────┐
  │ 🟢 otg-config-gen    │ (sequential, depends on A)
  └──────────┬───────────┘
             │
  ┌──────────────────────┐
  │ 🟡 snappi-script-gen │ (sequential, depends on previous)
  └──────────┬───────────┘
             │
  ┌──────────────────────┐
  │ 🔴 keng-licensing    │ (optional, independent)
  └──────────────────────┘

Config + Script Only (config_only):
  ┌──────────────────────┐
  │ 🟢 otg-config-gen    │ (entry point, existing infra)
  └──────────┬───────────┘
             │
  ┌──────────────────────┐
  │ 🟡 snappi-script-gen │ (depends on previous)
  └──────────┬───────────┘
             │
  ┌──────────────────────┐
  │ 🔴 keng-licensing    │ (optional)
  └──────────────────────┘

Deployment Only (deployment_only):
  ┌──────────────────────┐
  │ 🔵 ixia-c-deploy     │ (single agent)
  └──────────────────────┘

Script from Existing Config (script_only):
  ┌──────────────────────┐
  │ 🟡 snappi-script-gen │ (single agent, takes config as input)
  └──────────────────────┘

Licensing Only (licensing_only):
  ┌──────────────────────┐
  │ 🔴 keng-licensing    │ (single agent)
  └──────────────────────┘

Full Pipeline + Parallel Licensing (full_greenfield_with_licensing):
  ┌─────────────────────┐         ┌──────────────────────┐
  │ 🔵 ixia-c-deploy    │ ───┬──→ │ 🔴 keng-licensing    │ (parallel group A)
  └──────────┬──────────┘    │    └──────────────────────┘
             │               │
             │ (wait for all in group A)
             │
  ┌──────────────────────┐
  │ 🟢 otg-config-gen    │
  └──────────┬───────────┘
             │
  ┌──────────────────────┐
  │ 🟡 snappi-script-gen │
  └──────────────────────┘
```

**State Transitions:**
```
[Intent Validated]
    ↓
[Classify Use Case from intent.use_case field]
    ↓
[Determine Dispatch Sequence → Sub-agent Queue]
    ↓
[For each sub-agent in queue]:
    ├─ [Invoke Sub-agent]
    ├─ [Save Checkpoint]
    ├─ [User Approval Gate]
    │  ├─ [Yes] → Proceed to next
    │  ├─ [No] → End / Edit Intent & Restart
    │  └─ [Edit & Retry] → Modify agent input, re-run same agent
    │
[All sub-agents complete]
    ↓
[Generate Manifest + Summary]
    ↓
[✅ Run Complete]
```

**Parallel Dispatch Rules:**
- `ixia-c-deployment` and `keng-licensing` can run in parallel (no data dependency)
- `otg-config-generator` must complete before `snappi-script-generator` (generator depends on config)
- All other orderings are sequential
- Checkpoints are saved after each agent completes, regardless of parallelism
- User confirmation gates are serialized (one checkpoint at a time)

### Execution Rules
- **Conditional dispatch:** Sequence determined by `use_case` field in validated intent (see Conditional Dispatch Model above)
- **Parallel dispatch:** `ixia-c-deployment` and `keng-licensing` run in parallel when both are needed; all other agents run sequentially
- **Adaptive retry:** Retry based on sub-agent type and failure classification (see Adaptive Retry Strategy below)
- **Checkpoints between agents:** Saved after each agent completes, regardless of parallelism
- **User confirmation gate:** After each checkpoint (serialized, one at a time)

### Adaptive Retry Strategy

| Sub-Agent | Timeout | Max Retries | Rationale |
|-----------|---------|-------------|-----------|
| 🔵 `ixia-c-deployment` | 10min | 3 | Docker ops slow, transient-heavy (socket, disk, network) |
| 🟢 `otg-config-generator` | 2min | 2 | Config generation fast, validation-heavy |
| 🟡 `snappi-script-generator` | 1min | 1 | Deterministic, template-driven, low failure rate |
| 🟠 `keng-licensing` | 30sec | 1 | API-driven, quick response expected |

**Retry backoff:** Exponential → 2s, 4s, 8s between attempts

**max_wait_time_minutes precedence:**
- `max_wait_time_minutes` from the intent (default: 30) acts as a **global wall-clock budget** across all agents and all retries combined
- If an agent invocation would exceed the remaining budget, the orchestrator:
  - Skips remaining retries for that agent (fail fast)
  - Offers user two options: [Continue without this agent] or [Extend deadline]
- Example: User sets `max_wait_time_minutes: 5`, deployment starts, timeout is 10min per spec
  - After 4 minutes, deployment times out once, retries begin at 4m 2s, at 4m 6s, exceeds 5min budget
  - Orchestrator stops retrying, offers to continue without deployment or extend deadline

### Checkpoint Structure
```json
{
  "checkpoint_id": "ckpt_2_ixia-c-deployment",
  "sub_agent": "ixia-c-deployment",
  "agent_color": "🔵",
  "sequence": 2,
  "status": "success",

  "input": {
    "deployment_method": "docker_compose",
    "controller_url": "localhost:8443",
    "ports": [...]
  },

  "output": {
    "docker_compose_yml": "...",
    "location_map": {...},
    "ports": [...]
  },

  "timestamp": "2026-03-19T10:15:30Z",
  "duration_seconds": 45,
  "retry_count": 0,
  "warnings": [],

  "user_action": "approved",
  "user_action_timestamp": "2026-03-19T10:15:35Z"
}
```

**user_action values:**
- `"approved"` — User clicked [Yes], proceed to next agent
- `"rejected"` — User clicked [No], halt pipeline and return to intent editing
- `"edit_and_retry"` — User clicked [Edit & Retry], modified input params, re-invoked same agent (see Edit & Retry Behavior below)

**Edit & Retry Behavior:**
When user selects [Edit & Retry]:
1. **Display editable fields:** Show sub-agent input fields that user can modify (e.g., port speeds, controller URL)
2. **User modifies:** User edits one or more fields
3. **Re-invocation:** Orchestrator re-invokes sub-agent with modified input
4. **New retry attempt:** This counts as a retry (increments `retry_count`)
5. **Checkpoint handling:** The new output overwrites the previous checkpoint (same `checkpoint_id`, same `sequence`)
6. **User action recorded:** `user_action: "edit_and_retry"`, `user_action_timestamp` recorded

If max retries exceeded and user wants to [Edit & Retry], ask if they want to escalate to [Edit Intent] (which restarts the pipeline).

### User Confirmation Gate
After each successful checkpoint, display:
```
═══════════════════════════════════════════════════════════════
🔵 ixia-c-deployment: ✅ Success
═══════════════════════════════════════════════════════════════

Generated: docker-compose.yml (2KB)
Ports: te1:5555, te2:5556
Duration: 45 seconds

Does this look right?

   [1] Yes, proceed to next agent
   [2] No, stop and edit intent
   [3] Edit & Retry (modify deployment parameters and re-run)

Your choice? > _
```

**Option behavior:**
- `[1] Yes` → Save checkpoint with `user_action: "approved"`, proceed to next agent in queue
- `[2] No` → Save checkpoint with `user_action: "rejected"`, halt orchestration, return user to Intent editing (user can restart with edited intent)
- `[3] Edit & Retry` → Show editable fields (e.g., deployment method, port speeds), user modifies, orchestrator re-invokes same agent, loop back to confirmation gate

---

## Design Section 3: Checkpoint & Artifact System

### Purpose
Create persistent, structured records that are auditable and reusable.

### Directory Structure
```
orchestration_runs/
├── run_20260319_101530/
│   ├── intent.json                          # User's validated intent (not a checkpoint)
│   ├── manifest.json                        # Master execution record
│   ├── summary.md                           # Human-readable summary
│   ├── checkpoints/
│   │   ├── ckpt_0_ixia-c-deployment.json    # Sequence 0: deployment (if needed)
│   │   ├── ckpt_1_otg-config-generator.json # Sequence 1: config generation
│   │   ├── ckpt_2_snappi-script-gen.json    # Sequence 2: script generation
│   │   └── ckpt_3_keng-licensing.json       # Sequence 3: licensing (if needed)
│   └── outputs/
│       ├── docker-compose.yml               # From ckpt_0 (if applicable)
│       ├── otg_config.json                  # From ckpt_1 (if applicable)
│       ├── test_script.py                   # From ckpt_2 (if applicable)
│       └── infrastructure.yaml              # Generated by orchestrator from ckpt_0 + ckpt_1
```

**Numbering scheme:**
- `sequence` in checkpoint starts at 0 for the first agent invoked in the dispatch queue
- Checkpoint filenames match sequence: `ckpt_<sequence>_<agent_name>.json`
- For use cases with fewer agents (e.g., script-only), the sequence still starts at 0
- Intent validation is not a checkpoint; it happens in Phase 1 before dispatch

### Master Manifest (manifest.json)
```json
{
  "run_id": "run_20260319_101530",
  "user_intent_original": "Create BGP test, deploy Docker, get script + license",

  "timestamps": {
    "start": "2026-03-19T10:15:30Z",
    "end": "2026-03-19T10:22:15Z",
    "duration_seconds": 405
  },

  "intent_normalized": {...},

  "execution_flow": [
    {
      "sequence": 0,
      "sub_agent": "ixia-c-deployment",
      "agent_color": "🔵",
      "status": "success",
      "retry_count": 0,
      "duration_seconds": 45,
      "user_action": "approved",
      "user_action_timestamp": "2026-03-19T10:16:15Z",
      "output_size_bytes": 2048,
      "output_checksum": "sha256:abc123...",
      "warnings": []
    },
    {
      "sequence": 1,
      "sub_agent": "otg-config-generator",
      "agent_color": "🟢",
      "status": "success",
      "retry_count": 1,
      "first_attempt_error": "Missing port speed; user edited intent and retried",
      "duration_seconds": 30,
      "user_action": "approved",
      "user_action_timestamp": "2026-03-19T10:16:50Z",
      "warnings": []
    },
    {
      "sequence": 2,
      "sub_agent": "snappi-script-generator",
      "agent_color": "🟡",
      "status": "success",
      "retry_count": 0,
      "duration_seconds": 25,
      "user_action": "approved",
      "user_action_timestamp": "2026-03-19T10:17:30Z",
      "warnings": []
    },
    {
      "sequence": 3,
      "sub_agent": "keng-licensing",
      "agent_color": "🔴",
      "status": "success",
      "retry_count": 0,
      "duration_seconds": 15,
      "user_action": "approved",
      "user_action_timestamp": "2026-03-19T10:17:50Z",
      "warnings": ["License tier Developer exceeds recommended for 4 BGP sessions"]
    }
  ],

  "errors": [],
  "warnings": [
    "License: Developer tier will support only up to 2 BGP sessions; Team recommended"
  ],

  "final_status": "success",
  "output_files": [
    "outputs/docker-compose.yml",
    "outputs/otg_config.json",
    "outputs/test_script.py",
    "outputs/infrastructure.yaml"
  ]
}
```

### Human-Readable Summary (summary.md)
```markdown
# OTG Orchestration Run: BGP Test Deployment

**User Request:** Create BGP test with 2 ports, deploy with Docker, get script + license

**Execution Summary:**
- 🔵 Intent validated (2 clarifying questions)
- 🔵 Deployment: docker-compose.yml generated (1 retry, Docker socket issue)
- 🟢 Config: otg_config.json generated (aligned with port locations)
- 🟡 Script: test_bgp_convergence.py generated
- 🔴 Licensing: Developer tier may exceed limits for 4 BGP sessions

**Timeline:**
1. 10:15:30 — Intent intake complete
2. 10:16:15 — Deployment generated (45s)
3. 10:16:50 — Config generated (30s)
4. 10:17:30 — Script generated (25s)
5. 10:22:15 — Run complete (405s total)

**Warnings:**
- License: Developer tier will support only up to 2 BGP sessions; Team recommended for your 4 sessions

**Next Steps:**
1. Review docker-compose.yml in `outputs/`
2. Deploy with: `docker-compose -f outputs/docker-compose.yml up`
3. Run test: `python outputs/test_bgp_convergence.py`
4. (Optional) Upgrade license and re-run for cost estimate

**Artifacts:** All files saved to `orchestration_runs/run_20260319_101530/`
```

### Reusability for Future Runs
1. **Intent Templates:** Save successful intents → "Run template: BGP_deployment_docker"
2. **Pattern Library:** Analyze execution flows → "This pattern works well for protocol testing"
3. **Failure Recovery:** Record common failures → "When deployment times out, usually Docker socket issue"
4. **Metrics:** Track success rates, retry distributions, performance per sub-agent

### Infrastructure YAML Generation

**What is infrastructure.yaml?**
A YAML manifest that aggregates deployment and infrastructure details needed by `snappi-script-generator`. It is generated by the orchestrator (not by a sub-agent) after the deployment checkpoint completes.

**When is it generated?**
- If `ixia-c-deployment` is invoked and succeeds, the orchestrator extracts relevant fields from its checkpoint output and creates `infrastructure.yaml` before invoking the next agent

**Schema:**
```yaml
controller:
  url: "localhost:8443"
  protocol: "https"

ports:
  - name: "te1"
    location: "192.168.1.1:5555"
    speed: "100GE"
  - name: "te2"
    location: "192.168.1.1:5556"
    speed: "100GE"

deployment_manifest:
  method: "docker_compose"
  file_path: "outputs/docker-compose.yml"
  container_image: "keysight/ixia-c-one:latest"

generated_timestamp: "2026-03-19T10:16:15Z"
```

**Usage:**
`snappi-script-generator` reads `infrastructure.yaml` (plus `otg_config.json` from the previous checkpoint) to generate the final test script with correct controller endpoints and port locations.

### Agent Color Coding
- 🔵 `ixia-c-deployment` → Blue
- 🟢 `otg-config-generator` → Green
- 🟡 `snappi-script-generator` → Yellow
- 🟠 `keng-licensing` → Orange (revised from red to signal advisory, not error)

Applied to: console logs, summary markdown, manifest, checkpoint files. For non-emoji environments (log files, CI), use ASCII fallbacks: `[DEPLOY]`, `[CONFIG]`, `[SCRIPT]`, `[LICENSE]`.

---

## Design Section 4: Error Recovery Strategy

### Purpose
Handle transient failures intelligently; surface validation errors to the user.

### Error Classification

#### 1. Transient Errors (Retry Eligible)
- Timeouts, network hiccups, rate limiting
- Sub-agent service temporarily unavailable
- Recovery: **Retry with exponential backoff**

#### 2. Validation Errors (Fail-Fast)
- Invalid user intent (missing critical parameters)
- Incompatible parameter combinations
- Malformed output from upstream agent
- Recovery: **Ask user for clarification**

#### 3. State Mismatch (Offer Recovery)
- Downstream agent expects output upstream didn't produce
- Checkpoint corrupted or missing
- Recovery: **Offer user to retry from checkpoint or restart**

### Recovery Flow per Sub-Agent

| Sub-Agent | Example Transient | Example Validation | Recovery Options |
|-----------|------------------|-------------------|------------------|
| 🔵 `ixia-c-deployment` | Docker daemon down, disk full, network timeout | Invalid Docker image, conflicting ports | Retry / Edit Intent / Skip (use existing infra) |
| 🟢 `otg-config-generator` | API timeout, rate limit | Missing port count, conflicting protocol specs | Edit Intent / Retry / Abort |
| 🟡 `snappi-script-generator` | Template service down | Invalid OTG config structure | Retry from checkpoint / Edit Intent / Abort |
| 🔴 `keng-licensing` | License server timeout | Unknown license tier | Retry / Edit Intent / Abort |

### Recovery UI
```
🔵 ixia-c-deployment failed:
  Error: Connection timeout after 10 minutes

  [Transient Failure] Retrying... (Attempt 1/3)
  Waiting 2s before retry...

  [Transient Failure] Retrying... (Attempt 2/3)
  Waiting 4s before retry...

  [Transient Failure] Max retries exhausted.

  Recovery Options:
  1. [Edit Intent] — Change deployment parameters, then retry
  2. [Retry Now] — Retry with same parameters
  3. [Skip] — Skip deployment, use existing infrastructure
  4. [Abort] — Stop orchestration

  Your choice? > _
```

### Validation Error Example
```
🟢 otg-config-generator failed:
  Error: Validation error — 'port_speed' is required but missing

  The configuration generator needs to know the port speeds.
  Current intent has: port_count=2 but port_speed=[undefined]

  Recovery Options:
  1. [Edit Intent] — Specify port speeds and retry
  2. [Abort] — Stop orchestration

  Your choice? > _
```

---

## Design Section 5: Integration with Sub-agents & Testing

### Purpose
Define how orchestrator calls sub-agents, validates outputs, and enables testing.

### Sub-Agent Integration

**Invocation Pattern:**
```python
# Invoke sub-agent with context
skill_result = invoke_skill(
  skill="<sub_agent_name>",
  context={
    "intent": intent_object,
    "previous_checkpoints": [ckpt_1, ckpt_2, ...],
    "deployment_info": (if applicable)
  }
)

# Validate output schema
if not is_valid_schema(skill_result.output):
  raise ValidationError("Output doesn't match expected schema")

# Save checkpoint
save_checkpoint(
  sub_agent=skill_result.agent_name,
  input=skill_result.input,
  output=skill_result.output,
  status="success"
)
```

### Sub-Agent Output Schemas

Each sub-agent output must conform to its schema for orchestrator validation and checkpoint storage.

**1. ixia-c-deployment Output Schema**
```json
{
  "status": "success",
  "deployment_manifest": {
    "method": "docker_compose|containerlab",
    "file_path": "outputs/docker-compose.yml",
    "file_content": "...",
    "container_image": "keysight/ixia-c-one:latest"
  },
  "controller_url": "localhost:8443",
  "ports": [
    {"name": "te1", "location": "192.168.1.1:5555", "speed": "100GE"},
    {"name": "te2", "location": "192.168.1.1:5556", "speed": "100GE"}
  ],
  "warnings": []
}
```

**2. otg-config-generator Output Schema**
```json
{
  "status": "success",
  "otg_config": {
    "description": "BGP convergence test",
    "ports": [...],
    "devices": [...],
    "flows": [...],
    "protocols": {...}
  },
  "warnings": []
}
```

**3. snappi-script-generator Output Schema**
```json
{
  "status": "success",
  "script": {
    "file_path": "outputs/test_script.py",
    "file_content": "...",
    "entry_point": "main()",
    "supports_interactive": true
  },
  "assertions": [
    "bgp_session_established",
    "traffic_flowing_bidirectional"
  ],
  "warnings": []
}
```

**4. keng-licensing Output Schema** (Structured)
```json
{
  "status": "success",
  "recommendation": {
    "tier": "team|developer|system",
    "reason": "4 BGP sessions exceed Developer tier limit of 2",
    "seats_needed": 1,
    "exceeds_tier": "developer"
  },
  "cost_estimate": {
    "tier": "team",
    "annual_cost_usd": 5000,
    "currency": "USD"
  },
  "disclaimer": "Cost estimates are advisory. Please verify with Solutions Engineer.",
  "warnings": []
}
```

**Validation Flow:**
```python
# After sub-agent invocation, validate output
schema = get_schema_for_agent(agent_name)
if not jsonschema.validate(skill_result.output, schema):
  raise ValidationError(f"Output from {agent_name} doesn't match schema")

# Save to checkpoint
checkpoint.output = skill_result.output
checkpoint.output_size_bytes = len(json.dumps(checkpoint.output))
checkpoint.output_checksum = sha256(json.dumps(checkpoint.output))
```

### Testing Strategy

**1. Unit Tests** (Logic)
- Intent validation (normalize, validate against capabilities)
- State machine transitions
- Checkpoint schema validation
- Artifact manifest generation

**2. Integration Tests** (With Mock Sub-Agents)
- Mock sub-agent outputs
- Test orchestration flow (without real deployments)
- Verify checkpoint progression
- Verify error recovery paths

**3. End-to-End Tests** (Optional)
- Real sub-agent invocation (safe, non-destructive)
- Full pipeline execution
- Artifact verification

**4. Artifact Validation**
- Manifest structure integrity
- Checkpoint checksums
- Output file existence

### Transport Adapter Layer

To ensure platform-agnostic design, the orchestrator uses a **transport adapter** that abstracts sub-agent invocation. Both Claude Code and future SDK implementations use the same interface.

**SubAgentTransport Interface** (language-agnostic contract):
```python
class SubAgentTransport:
    """Abstract transport for invoking sub-agents."""

    def invoke(
        self,
        agent_name: str,
        context: dict
    ) -> SubAgentResult:
        """
        Invoke a sub-agent.

        Args:
            agent_name: skill name (e.g., "otg-config-generator")
            context: normalized intent + previous checkpoints

        Returns:
            SubAgentResult: structured output + metadata

        Raises:
            SubAgentError: if invocation fails
        """
        pass

    def supports_interactive_confirmation(self) -> bool:
        """Return True if transport supports user confirmation gates."""
        pass

    def get_checkpoint_timeout(self, agent_name: str) -> int:
        """Return timeout in seconds for this agent."""
        pass
```

**Claude Code Implementation:**
```python
class SkillTransport(SubAgentTransport):
    def invoke(self, agent_name, context):
        # Use Skill tool to invoke sub-agent
        result = skill(skill=agent_name, context=context)
        return SubAgentResult.from_skill_result(result)

    def supports_interactive_confirmation(self):
        return True  # Claude Code is interactive
```

**Anthropic SDK Implementation** (future):
```python
class SDKTransport(SubAgentTransport):
    def invoke(self, agent_name, context):
        # Use SDK tools to invoke sub-agent
        result = self.sdk_client.agents.invoke(
            agent_id=self.agent_ids[agent_name],
            input=context
        )
        return SubAgentResult.from_sdk_result(result)

    def supports_interactive_confirmation(self):
        return False  # SDK may not support interactive confirmation
```

**Invariants (both platforms):**
- State machine logic unchanged
- Intent validation unchanged
- Checkpoint structure unchanged (JSON schema)
- Artifact format unchanged
- Error recovery strategy unchanged
- Sub-agent output schemas unchanged

**Design Implications:**
- Orchestrator is decoupled from transport (dependency injection)
- SDK implementation will need to handle non-interactive confirmation differently (e.g., pre-configured approvals, async confirmation)
- Checkpoints and artifacts are transport-independent (pure JSON/YAML)

---

## Non-Functional Requirements

| Requirement | Target | Rationale |
|------------|--------|-----------|
| **Reliability** | 99% checkpoint save success | Artifact integrity is critical |
| **Performance** | Full pipeline < 5 min (typical) | User patience for interactive orchestration |
| **Observability** | Structured logs + artifacts | Debugging and auditability |
| **Scalability** | Support 10+ sequential agents | Future expansion to more use cases |
| **Reusability** | Templates + pattern library | Reduce repetitive runs |
| **SDK Migration** | Zero logic changes | Platform agnostic design |

---

## Assumptions & Constraints

**Assumptions:**
- Sub-agent failures are classifiable as transient (retry-eligible) or deterministic (fail-fast)
- Intent is well-formed and validated before dispatch begins
- User is present for confirmation gates (synchronous, Claude Code only; SDK may differ)
- Artifact storage is persistent (local filesystem or cloud)
- Sub-agent output conforms to documented schemas

**Constraints:**
- Parallel dispatch limited to independent agents (e.g., deployment + licensing). Non-independent agents run sequentially.
- No cross-agent retry (if agent at sequence N fails, restart from sequence N, not sequence 0)
- Confirmation gates require synchronous user interaction (Claude Code); SDK transport may need alternative confirmation strategy
- Sub-agent invocations are synchronous (no async/fire-and-forget)

---

## Success Criteria

1. ✅ Intent is validated upfront → no surprises during execution
2. ✅ Checkpoints saved after each sub-agent → resumable at any stage
3. ✅ Error recovery is intelligent → transient vs validation vs state errors handled appropriately
4. ✅ Structured artifacts → complete audit trail for debugging and reuse
5. ✅ User confirmation gates → transparency, user control
6. ✅ Architecture is SDK-agnostic → minimal changes for future migration
7. ✅ Color-coded agents → visual clarity in logs and summaries

---

## Implementation Roadmap

| Phase | Task | Acceptance Criteria | Dependencies |
|-------|------|-------------------|--------------|
| 1 | Implement intent validation | Intent schema validates all 6 use cases from AGENT_ORCHESTRATION_PLAN.md; unit tests pass | None |
| 2 | Implement conditional dispatch engine | State machine correctly selects sub-agent sequence for all 6 use cases; unit tests | Phase 1 |
| 3 | Implement checkpoint & artifact system | Checkpoints saved with correct numbering; manifest generated; human summary readable | Phase 2 |
| 4 | Implement error recovery | Transient/validation/state errors handled correctly; recovery UI tested | Phase 2 |
| 5 | Implement transport adapter layer | SlillTransport and mock SDK transport both pass same test suite; orchestrator decoupled from transport | Phase 3 |
| 6 | Integration test full pipeline | Run all 6 use cases end-to-end with real sub-agents; artifacts verified | Phase 5 |
| 7 | User acceptance test | Users run greenfield + existing-infra scenarios; confirm UX and approvals work | Phase 6 |
| 8 | SDK migration prep | Design SDK transport implementation; prototype with Anthropic SDK | Phase 5 |

**Critical path:** Phase 1 → 2 → 3 → 5 → 6 → 7 (8 is parallel with 6-7)

---

## References

- [AGENT_ORCHESTRATION_PLAN.md](/Users/ashwin.joshi/kengotg/AGENT_ORCHESTRATION_PLAN.md)
- [Sub-agent Skills](/) — ixia-c-deployment, otg-config-generator, snappi-script-generator, keng-licensing

