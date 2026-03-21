# Agent Evaluation Sets

This directory contains structured evaluation question sets for each subagent. Use these to assess agent quality, validate functionality, and measure performance.

## Overview

| Agent | Eval File | Color | Focus Area | Questions |
|-------|-----------|-------|-----------|-----------|
| **ixia-c-deployment-agent** | `ixia-c-deployment-agent-eval.json` | 🔵 Blue | Infrastructure provisioning & validation | 5 |
| **otg-config-generator-agent** | `otg-config-generator-agent-eval.json` | 🟢 Green | Intent → OTG config translation | 5 |
| **snappi-script-generator-agent** | `snappi-script-generator-agent-eval.json` | 🟣 Purple | Config → executable script generation | 5 |
| **keng-licensing-agent** | `keng-licensing-agent-eval.json` | 🟠 Orange | Licensing cost estimation & recommendations | 5 |

**Total Evaluation Questions:** 20 (5 per agent)

---

## Evaluation Structure

Each eval set follows this JSON schema:

```json
{
  "agent_name": "...",
  "eval_set_version": "1.0",
  "created": "2026-03-19",
  "description": "...",
  "total_questions": 5,
  "eval_questions": [
    {
      "id": 1,
      "category": "happy_path | error_handling | edge_case | ...",
      "question": "User prompt or scenario",
      "expected_outputs": ["output 1", "output 2", ...],
      "success_criteria": ["criterion 1", "criterion 2", ...]
    },
    ...
  ]
}
```

---

## Question Categories by Agent

### 🔵 ixia-c-deployment-agent
1. **Happy Path** — Deploy for BGP with Docker Compose
2. **Containerlab Variant** — Deploy with Containerlab for LAG testing
3. **Error Handling** — Conflicting deployment requirements
4. **Integration Validation** — Port mapping format for downstream agents
5. **Health Check Edge Case** — Controller unreachable during health checks

**Focus:** Correctness of deployment manifests, health validation, port alignment

---

### 🟢 otg-config-generator-agent
1. **Happy Path** — Convert BGP test intent to OTG config
2. **Infrastructure Injection** — Port location injection from deployment agent
3. **Multi-Protocol Complexity** — BGP + ISIS + LACP in single config
4. **Error Handling (Ambiguity)** — Vague user intent with missing information
5. **Validation & Assertions** — Realistic and measurable assertions

**Focus:** Intent parsing, protocol configuration, assertion feasibility, infrastructure alignment

---

### 🟣 snappi-script-generator-agent
1. **Happy Path** — Generate standalone Snappi script from OTG config
2. **Error Handling** — Connection failure to controller
3. **Protocol Setup Verification** — BGP state polling and convergence timeout
4. **Metrics & Assertions** — Traffic collection and no-loss assertion
5. **Cleanup & Reporting** — Graceful cleanup and JSON report generation

**Focus:** Script correctness, error handling, protocol orchestration, resource cleanup

---

### 🟠 keng-licensing-agent
1. **Happy Path (Small Scale)** — POC lab licensing (2×10GE, traffic-only)
2. **Multi-Tier Comparison** — Developer/Team/System cost comparison
3. **Protocol Session Edge Case** — High session count (64 BGP) cost calculation
4. **Optimization Suggestions** — Cost reduction through protocol minimization
5. **Disclaimer & Accuracy** — SE disclaimer prominence and clarity

**Focus:** Cost accuracy, tier recommendations, optimization guidance, legal/business compliance

---

## How to Use Evaluation Sets

### Manual Evaluation
1. Read each question in the eval set
2. Invoke the agent with the scenario
3. Assess outputs against success criteria
4. Document pass/fail and notes

### Automated Evaluation (with LLM-as-Judge)
1. Parse eval set JSON
2. Invoke agent with each question
3. Use another LLM (Claude, GPT, etc.) to judge outputs against criteria
4. Aggregate scores and produce report

### Example Manual Run

```bash
# Question: eval-set[0] for ixia-c-deployment-agent
# Invoke the agent
@ixia-c-deployment-agent Deploy Ixia-c for BGP testing with Docker Compose. Generate docker-compose.yml with 2 ports for traffic generation and protocol emulation.

# Assess output:
# ✅ docker-compose.yml generated?
# ✅ Services include ixia-c-one, controller, traffic-engine, protocol-engine?
# ✅ Port mapping present?
# ✅ Health check passed?
```

---

## Success Criteria Grading

Each eval question has **success criteria** that should all be satisfied for a pass:

- **✅ All criteria met** → PASS
- **⚠️ 80%+ criteria met** → PASS_WITH_NOTES (document missing criteria)
- **❌ <80% criteria met** → FAIL (agent needs improvement)

---

## Integration with Skills

Eval sets test the agents, which wrap the underlying skills:

```
Eval Question → Agent → Skill → Output
                                    ↓
                            Assess against success_criteria
```

If an agent fails an eval question:
- Check if it's a skill issue (skill returns invalid output)
- Check if it's an agent issue (agent doesn't use skill correctly)
- Check if it's an integration issue (agent-skill interface mismatch)

---

## Extending Eval Sets

To add more eval questions:

1. **Identify gap** — What scenario is not covered?
2. **Create question** — Clear user intent or scenario
3. **Define expected outputs** — What should agent produce?
4. **Define success criteria** — How to measure success?
5. **Add to eval set** — Update the JSON file, increment `total_questions`

Example:

```json
{
  "id": 6,
  "category": "new_category",
  "question": "User intent...",
  "expected_outputs": ["output 1", ...],
  "success_criteria": ["criterion 1", ...]
}
```

---

## Metrics & Reporting

Track agent performance over time:

| Metric | Definition |
|--------|-----------|
| **Pass Rate** | % of eval questions passed |
| **Category Pass Rate** | % passed by category (e.g., error_handling pass rate) |
| **Time to Pass** | How long agent takes to answer question |
| **Output Quality** | Subjective assessment (1-5 scale) of output clarity and completeness |

---

## Agent Colors (Verified Unique)

```
🔵 Blue       → ixia-c-deployment-agent
🟢 Green      → otg-config-generator-agent
🟣 Purple     → snappi-script-generator-agent
🟠 Orange     → keng-licensing-agent
```

---

## Eval Question Breakdown

### 🔵 **ixia-c-deployment-agent** (Infrastructure)
| Q | Category | Focus |
|---|----------|-------|
| 1 | Happy Path | Docker Compose deployment + port mapping |
| 2 | Containerlab | Containerlab topology with LAG + ISIS |
| 3 | Error Handling | Conflicting deployment requirements |
| 4 | Integration | Port mapping format alignment |
| 5 | Edge Case | Health check failure (controller unreachable) |

### 🟢 **otg-config-generator-agent** (Intent→Config)
| Q | Category | Focus |
|---|----------|-------|
| 1 | Happy Path | BGP convergence test translation |
| 2 | Infrastructure | Port location injection validation |
| 3 | Complexity | Multi-protocol (BGP+ISIS+LACP) config |
| 4 | Error Handling | Vague/ambiguous user intent |
| 5 | Validation | Assertion feasibility & timeout realism |

### 🟣 **snappi-script-generator-agent** (Config→Script)
| Q | Category | Focus |
|---|----------|-------|
| 1 | Happy Path | Standalone Python script generation |
| 2 | Error Handling | Connection failure to controller |
| 3 | Protocol Setup | BGP state polling & convergence timeout |
| 4 | Metrics | Traffic assertion & no-loss validation |
| 5 | Cleanup | Resource cleanup & JSON reporting |

### 🟠 **keng-licensing-agent** (Cost Estimation)
| Q | Category | Focus |
|---|----------|-------|
| 1 | Happy Path | POC licensing (2×10GE, traffic-only) |
| 2 | Comparison | Developer/Team/System tier costs |
| 3 | Edge Case | High protocol session count (64 BGP) |
| 4 | Optimization | Cost reduction suggestions |
| 5 | Compliance | SE disclaimer & legal accuracy |

---

## Quick Test & Full Evaluation

### Quick Test
```bash
# Run one eval question for an agent
@ixia-c-deployment-agent Deploy Ixia-c for BGP testing with Docker Compose...
# Compare output to expected_outputs + success_criteria in eval-sets/ixia-c-deployment-agent-eval.json
```

### Full Evaluation
```bash
# Test all 5 questions for each agent
# Track pass/fail rate per category
# Document any failures or improvements needed
```

### With LLM-as-Judge (Future)
```python
# Parse eval set JSON
# Invoke agent for each question
# Use Claude/LLM to judge outputs
# Generate performance report with pass rate, score, notes
```

---

## Key Eval Insights

✅ **Coverage:** Each agent tested on happy path, error handling, edge cases, and integration points
✅ **Specificity:** Questions are concrete scenarios, not generic (e.g., "2×100GE + 8 BGP sessions" not "test licensing")
✅ **Measurability:** Success criteria are objective and verifiable
✅ **Completeness:** 20 total questions ensure thorough agent validation

---

## Version History

- **v1.0** (2026-03-19): Initial eval sets, 5 questions per agent, 20 total questions
- Ready for: Agent evaluation, performance tracking, skill validation

---

## References

- **Agent Specs:** `./../*.md` (agent specifications)
- **Orchestration Plan:** `../../AGENT_ORCHESTRATION_PLAN.md`
- **Skills:** Available via `/agents list` in Claude Code

