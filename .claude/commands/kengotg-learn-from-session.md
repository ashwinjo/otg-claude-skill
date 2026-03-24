---
name: kengotg-learn-from-session
description: Capture session learnings into fixes.md and update skill documentation
disable-model-invocation: false
allowed-tools: []
---

# Learn From Session

Systematically capture learnings from your testing sessions to improve agent behavior and skill quality over time.

## Overview

This command helps you:
1. **Document mistakes** — Root cause analysis of failures encountered
2. **Capture workarounds** — Solutions that fixed issues
3. **Update fixes.md** — Institutional memory for the project
4. **Improve skills** — Update SKILL.md with lessons learned
5. **Build agent feedback loops** — Agents learn from past mistakes

---

## What Gets Documented

### Learnings to Capture

- ✅ **Configuration issues** — What OTG config fields are/aren't supported in ixia-c-one
- ✅ **Agent mistakes** — When deployment, config, or script generation failed
- ✅ **Version incompatibilities** — Features not supported in certain controller versions
- ✅ **Workarounds** — How issues were resolved (e.g., using `deserialize()` instead of `loads()`)
- ✅ **API differences** — Snappi SDK API nuances (methods, field names, error handling)
- ✅ **Performance insights** — Throughput, latency, resource consumption
- ✅ **Best practices** — What approaches worked well (e.g., programmatic traffic stop vs. duration-based)

### What NOT to Capture

- ❌ User preferences or conversational context
- ❌ Temporary debug output or test artifacts
- ❌ Obvious bugs that are already fixed
- ❌ Hypothetical future improvements

---

## Usage Pattern

### 1. Review Your Session

After completing a test or hitting an issue:
```
/kengotg-learn-from-session
```

The command will guide you through:
1. **Summarize what happened** — What did you test? What broke?
2. **Root cause** — Why did it fail? (version issue, unsupported feature, API misuse, etc.)
3. **Solution** — How did you fix it?
4. **Prevention** — How to avoid this in the future?

### 2. Choose Affected Skills

Select which skills this learning affects:
- `snappi-script-generator` — Script generation, Snappi API issues
- `otg-config-generator` — OTG schema, config validation
- `ixia-c-deployment` — Deployment, controller compatibility
- `ixnetwork-to-keng-converter` — Migration, feature support
- `keng-licensing` — Licensing calculations

### 3. Output

Two files are updated:

**fixes.md** — New entry with:
```markdown
### [Category] [Issue Title]
**Date:** YYYY-MM-DD
**Agent:** [Which agent encountered this]
**Symptom:** [What failed]
**Root Cause:** [Why]
**Solution:** [How it was fixed]
**Prevention:** [Avoid next time]
**Status:** ✅ Fixed | 🔧 Monitoring | ⚠️ Partial fix
```

**Skill SKILL.md** — Updated with:
- New section in "Known Limitations" or "Best Practices"
- Code example showing the fix
- Reference to fixes.md entry

---

## Example: Recent Session Learning

### Your Session
**What:** Containerlab B2B loopback test
**Issue:** OTG config with latency/loss metrics rejected by ixia-c-one
**Root Cause:** ixia-c-one doesn't support flow-level latency/loss metrics
**Solution:** Removed unsupported fields, used port-level metrics only
**Prevention:** Add validation check in otg-config-generator for ixia-c-one targets

### Fixes.md Entry
```markdown
### [Config Validation] ixia-c-one Metric Field Incompatibility
**Date:** 2026-03-22
**Agent:** otg-config-generator-agent
**Symptom:** OTG config push rejected with "Latency mode store_forward not supported" error
**Root Cause:** ixia-c-one container (keng-controller v1.48.0-5) doesn't support:
  - Flow-level latency metrics (any mode)
  - Flow-level loss metrics
  - These fields work in full ixia-c CP+DP but not in ixia-c-one bundle
**Solution:** Remove `metrics.latency` and `metrics.loss` fields when target is ixia-c-one
  Only use `metrics.enable: true` (basic counters) and rely on port-level stats
**Prevention:**
  1. Add config validation check: if deployment_type == "ixia-c-one", remove unsupported fields
  2. Document in otg-config-generator/SKILL.md: "Metric field support by deployment type"
  3. Add eval case: "Generate config for ixia-c-one with latency metrics (should auto-remove)"
**Status:** ✅ Fixed (workaround implemented in snappi-script-generator v1.1)
```

### Skill Update (snappi-script-generator/SKILL.md)
```markdown
## Known Limitations by Deployment Type

### ixia-c-one (All-in-one bundle)
- ❌ Flow-level latency metrics (store_forward, cut_through, all modes)
- ❌ Flow-level loss metrics
- ✅ Port-level frame counters
- ✅ Basic flow metrics (enable: true)

**Workaround:** If OTG config includes unsupported fields, the script generator
removes them before pushing to the controller. See fixes.md entry on metric field compatibility.

### Full ixia-c (CP+DP, Docker Compose)
- ✅ All metric types supported
- ✅ Latency modes: store_forward, cut_through
- ✅ Flow-level and port-level metrics
```

---

## Workflow: Learn → Fix → Document → Improve

```
Your Test Session
       ↓
  Identify Learning
  (what broke? why?)
       ↓
  /kengotg-learn-from-session
       ↓
  Add to fixes.md
  (root cause, solution, prevention)
       ↓
  Update Skill SKILL.md
  (document limitation, add example)
       ↓
  Add eval case
  (test case to prevent regression)
       ↓
  Next agent session
  (reads fixes.md at startup, avoids same mistake)
```

---

## Template: Quick Learning Capture

Copy this and fill in after each test:

```markdown
**Session Date:** [YYYY-MM-DD]
**What Happened:** [Test name, scenario]
**Issue Encountered:** [Error message or behavior]
**Root Cause:** [Why did it fail?]
**Solution Applied:** [How you fixed it]
**Prevention Strategy:** [How to avoid next time]
**Affected Skill:** [snappi-script-generator | otg-config-generator | ixia-c-deployment | ...]
**Eval Case Needed:** [Yes/No] — [What test case should prevent regression?]
```

---

## Files Updated

- **fixes.md** — Project root, agent learning log
  - Format: Standard entry with Date, Agent, Symptom, Root Cause, Solution, Prevention, Status
  - One entry per distinct issue
  - Organized by category (Config Validation, Script Generation, Deployment, etc.)

- **Skill SKILL.md** — `.claude/skills/<skill-name>/SKILL.md`
  - Add to "Known Limitations" section
  - Document the constraint and workaround
  - Reference fixes.md entry

- **Skill evals.json** — `.claude/skills/<skill-name>/evals/evals.json`
  - Add new test case that would catch the issue
  - Prevents regression in future agent improvements

---

## Status Codes

- `✅ Fixed` — Issue is resolved, fix is implemented and tested
- `🔧 Monitoring` — Fix implemented, but monitoring for edge cases
- `⚠️ Partial fix` — Workaround exists, but root cause needs deeper fix
- `🚧 In Progress` — Fix is being implemented

---

## Example: Full Learning Cycle

### Session 1: Containerlab B2B Test (2026-03-22)
```
Issue: cfg.loads() method doesn't exist on snappi.Config
Root Cause: Snappi SDK uses cfg.deserialize() not cfg.loads()
Solution: Changed script to use deserialize()
Prevention: Add check in snappi-script-generator for correct Snappi API usage
```

Documented in:
- `fixes.md` — Entry: "Snappi API: Config deserialization method"
- `snappi-script-generator/SKILL.md` — Updated "Snappi SDK API Reference" section
- `snappi-script-generator/evals/evals.json` — Added test case

### Session 2: Next Agent Session (2026-03-23)
Agent reads fixes.md at startup, sees the entry, **avoids the mistake automatically**.

---

## Key Principle

> **Mistakes → Documentation → Prevention**

Each failure becomes:
1. A fixes.md entry (for all agents to learn)
2. A skill update (for users to understand constraints)
3. An eval test case (to prevent regression)

Over time, agents get smarter and skills get more robust.

---

## See Also

- `fixes.md` — View all captured learnings
- `AGENT_ORCHESTRATION_PLAN.md` — Agent learning strategy
- `.claude/skills/*/SKILL.md` — Skill best practices and limitations
