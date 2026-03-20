# OTG Orchestrator: Robust Execution Design

**Date:** 2026-03-19
**Status:** Design Review
**Scope:** Claude Code orchestrator → future Anthropic SDK migration

---

## Executive Summary

This design establishes a **hybrid orchestrator** that validates user intent upfront, executes sub-agents sequentially with intelligent checkpointing, and collects structured artifacts throughout execution. The orchestrator is robust (adaptive retry, smart recovery), auditable (complete artifact trail), and reusable (templates and patterns for future runs).

The orchestrator bridges Claude Code (immediate) and Anthropic SDK (future), ensuring architecture is platform-agnostic.

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

### State Machine Diagram
```
[Intent Validated]
    ↓
[🔵 Dispatch ixia-c-deployment] (if needed)
    ↓
[Checkpoint 1] → [User Approval?] → No → [End / Edit Intent]
    ↓ Yes
[🟢 Dispatch otg-config-generator]
    ↓
[Checkpoint 2] → [User Approval?] → No → [End / Edit Intent]
    ↓ Yes
[🟡 Dispatch snappi-script-generator]
    ↓
[Checkpoint 3] → [User Approval?] → No → [End / Edit Intent]
    ↓ Yes
[🔴 Dispatch keng-licensing]
    ↓
[Checkpoint 4] → [User Approval?] → No → [End]
    ↓ Yes
[✅ Run Complete] → [Generate Manifest] → [Done]
```

### Execution Rules
- **Sequential dispatch:** Each sub-agent waits for previous to complete
- **Adaptive retry:** Retry based on sub-agent type and failure classification
- **Checkpoints between agents:** No checkpoint → no progress guarantee
- **User confirmation gate:** After each successful checkpoint

### Adaptive Retry Strategy

| Sub-Agent | Timeout | Max Retries | Rationale |
|-----------|---------|-------------|-----------|
| 🔵 `ixia-c-deployment` | 10min | 3 | Docker ops slow, transient-heavy (socket, disk, network) |
| 🟢 `otg-config-generator` | 2min | 2 | Config generation fast, validation-heavy |
| 🟡 `snappi-script-generator` | 1min | 1 | Deterministic, template-driven, low failure rate |
| 🔴 `keng-licensing` | 30sec | 1 | API-driven, quick response expected |

**Retry backoff:** Exponential → 2s, 4s, 8s between attempts

### Checkpoint Structure
```json
{
  "checkpoint_id": "ckpt_1_ixia-c-deployment",
  "sub_agent": "ixia-c-deployment",
  "agent_color": "🔵",
  "sequence": 1,
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

  "user_action": "approved"
}
```

### User Confirmation Gate
After each successful checkpoint, display:
```
🔵 ixia-c-deployment: ✅ Success
   Generated: docker-compose.yml (2KB)
   Ports: te1:5555, te2:5556

   Does this look right?
   [Yes] [No] [Edit & Retry]
```

---

## Design Section 3: Checkpoint & Artifact System

### Purpose
Create persistent, structured records that are auditable and reusable.

### Directory Structure
```
orchestration_runs/
├── run_<timestamp>/
│   ├── intent.json                    # User's validated intent
│   ├── manifest.json                  # Master execution record
│   ├── summary.md                     # Human-readable summary
│   ├── checkpoints/
│   │   ├── ckpt_1_intent_validated.json
│   │   ├── ckpt_2_ixia-c-deployment.json
│   │   ├── ckpt_3_otg-config-generator.json
│   │   ├── ckpt_4_snappi-script-generator.json
│   │   └── ckpt_5_keng-licensing.json
│   └── outputs/
│       ├── docker-compose.yml
│       ├── otg_config.json
│       ├── test_script.py
│       └── infrastructure.yaml
```

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
      "sequence": 1,
      "sub_agent": "ixia-c-deployment",
      "agent_color": "🔵",
      "status": "success",
      "retry_count": 0,
      "duration_seconds": 45,
      "user_action": "approved",
      "output_size_bytes": 2048,
      "output_checksum": "sha256:abc123..."
    },
    {
      "sequence": 2,
      "sub_agent": "otg-config-generator",
      "agent_color": "🟢",
      "status": "success",
      "retry_count": 1,
      "first_attempt_error": "Missing port speed; retried",
      "duration_seconds": 30,
      "user_action": "approved"
    },
    ...
  ],

  "errors": [],
  "warnings": [
    "License will exceed Developer tier limits; Team recommended"
  ],

  "final_status": "success",
  "output_files": [
    "outputs/docker-compose.yml",
    "outputs/otg_config.json",
    "outputs/test_script.py"
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

### Agent Color Coding
- 🔵 `ixia-c-deployment` → Blue
- 🟢 `otg-config-generator` → Green
- 🟡 `snappi-script-generator` → Yellow
- 🔴 `keng-licensing` → Red

Applied to: console logs, summary markdown, manifest, checkpoint files

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

**Output Validation:**
Each sub-agent output must conform to a schema:
- `ixia-c-deployment` → deployment manifest (docker-compose.yml, port map)
- `otg-config-generator` → OTG JSON config
- `snappi-script-generator` → Python script (executable, with assertions)
- `keng-licensing` → license recommendation, cost estimate

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

### Future SDK Integration

**Current (Claude Code):**
```python
invoke_skill(skill="otg-config-generator", context={...})
```

**Future (Anthropic SDK):**
```python
agent = OrchestratorAgent()
result = agent.run(user_intent=request, max_iterations=10)
```

**Invariants (both platforms):**
- State machine logic unchanged
- Intent validation unchanged
- Checkpoint structure unchanged
- Artifact format unchanged
- Error recovery strategy unchanged

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
- Sub-agents are reliable (invocations succeed or fail deterministically)
- Intent is well-formed after validation phase
- User is present for confirmation gates (synchronous)
- Artifact storage is persistent (local filesystem or cloud)

**Constraints:**
- Sequential sub-agent dispatch (parallelization not yet supported)
- No cross-agent retry (if agent 3 fails, start from agent 3, not agent 1)
- Confirmation gates require user interaction (not auto-confirmed)

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

## Rollout Plan

1. **Implement Phase 1:** Intent intake & validation
2. **Implement Phase 2:** State machine & orchestration
3. **Implement Phase 3:** Checkpoint & artifact system
4. **Implement Phase 4:** Error recovery
5. **Implement Phase 5:** Sub-agent integration & testing
6. **Integration test** across all phases
7. **User acceptance test** with real use cases
8. **Prepare for SDK migration** (architecture review, SDK adapter layer design)

---

## References

- [AGENT_ORCHESTRATION_PLAN.md](/Users/ashwin.joshi/kengotg/AGENT_ORCHESTRATION_PLAN.md)
- [Sub-agent Skills](/) — ixia-c-deployment, otg-config-generator, snappi-script-generator, keng-licensing

