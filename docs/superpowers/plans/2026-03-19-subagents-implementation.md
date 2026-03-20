# Phase 6: Sub-Agent Implementation Plan

> **Goal:** Create 4 independent sub-agents in `.claude/agents/` that wrap existing skills and can be called by orchestrator or directly by users.

**Architecture:** Each sub-agent:
1. Takes orchestrator context as input (intent, previous checkpoints)
2. Calls its corresponding skill
3. Returns checkpoint-ready output with metadata
4. Can be invoked standalone by users

---

## Sub-Agents to Create

### 1. ixia-c-deployment Agent
- **Folder:** `.claude/agents/ixia-c-deployment/`
- **Purpose:** Deploy Ixia-c infrastructure
- **Calls:** `ixia-c-deployment` skill
- **Input:** Intent (deployment method, controller URL, ports)
- **Output:** docker-compose.yml, port mappings, controller details
- **Checkpoint Data:** deployment manifest, port locations

### 2. otg-config-generator Agent
- **Folder:** `.claude/agents/otg-config-generator/`
- **Purpose:** Generate OTG configurations
- **Calls:** `otg-config-generator` skill
- **Input:** Intent (protocols, ports, sessions) + deployment info from checkpoint 0
- **Output:** otg_config.json with all protocol/traffic setup
- **Checkpoint Data:** OTG config + warnings

### 3. snappi-script-generator Agent
- **Folder:** `.claude/agents/snappi-script-generator/`
- **Purpose:** Generate Snappi test scripts
- **Calls:** `snappi-script-generator` skill
- **Input:** OTG config from checkpoint 1 + infrastructure details
- **Output:** test_*.py (executable Snappi script)
- **Checkpoint Data:** Script content + assertions + warnings

### 4. keng-licensing Agent
- **Folder:** `.claude/agents/keng-licensing/`
- **Purpose:** Provide license cost estimates
- **Calls:** `keng-licensing` skill
- **Input:** Test config (ports, speeds, protocols, sessions)
- **Output:** License recommendation, cost estimate, disclaimer
- **Checkpoint Data:** Recommendation + cost + warnings

---

## Each Sub-Agent Folder Structure

```
.claude/agents/AGENT_NAME/
├── agent.json              # Agent metadata
├── handler.py              # Entry point (invoke_agent)
├── README.md               # Agent documentation
└── tests.py                # Unit tests (optional)
```

---

## Agent Entry Point Pattern

```python
def invoke_agent(
    context: Dict[str, Any],
    interactive: bool = True
) -> Dict[str, Any]:
    """
    Invoke sub-agent.

    Args:
        context: {
            "intent": Intent dict,
            "previous_checkpoints": List[checkpoint JSON],
            "orchestrator_run_id": str (optional)
        }
        interactive: bool

    Returns:
        {
            "status": "success" | "error",
            "checkpoint_id": "ckpt_N_agent_name",
            "output": {...},
            "error": str (if failed),
            "warnings": [...],
            "duration_seconds": float
        }
    """
```

---

## Implementation Sequence

1. **Task 1:** Create ixia-c-deployment sub-agent
2. **Task 2:** Create otg-config-generator sub-agent
3. **Task 3:** Create snappi-script-generator sub-agent
4. **Task 4:** Create keng-licensing sub-agent
5. **Task 5:** Integration tests (all 4 agents working together + orchestrator)
6. **Task 6:** Update orchestrator transport to call sub-agents instead of skills

---

## Key Design Points

- **Idempotent:** Sub-agents can be called multiple times with same inputs
- **Checkpoint-Ready:** Output includes all data needed for checkpoint
- **Context-Aware:** Each agent knows its sequence number and previous results
- **Error Classification:** Failures classified as transient/validation/terminal
- **Standalone Callable:** Can be invoked directly without orchestrator
- **Logging:** All invocations logged for debugging

---

## Success Criteria

- ✅ 4 sub-agent folders created in `.claude/agents/`
- ✅ Each has `agent.json`, `handler.py`, `README.md`
- ✅ Each calls its corresponding skill
- ✅ Each returns checkpoint-ready output
- ✅ Each can be called standalone by users
- ✅ Integration tests passing
- ✅ Orchestrator updated to dispatch to sub-agents

