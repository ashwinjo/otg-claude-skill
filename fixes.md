# Agent Learning & Fixes Log

This file documents mistakes discovered by Claude agents during execution, their root causes, and solutions implemented.
**Update this file whenever an issue is discovered and fixed.**

## Format

```
### [Category] Issue Title
**Date:** YYYY-MM-DD
**Agent:** [Agent name or context]
**Symptom:** What went wrong
**Root Cause:** Why it happened
**Solution:** How it was fixed
**Prevention:** How to avoid this in future
**Status:** ✅ Fixed | 🔧 Monitoring | ⚠️ Partial fix
```

---

## Issues & Fixes

*(None yet — fill as issues are discovered and resolved)*

---

## Categories

- **Port Alignment** — Port mapping, location mismatches between agents
- **Script Generation** — Python syntax, Snappi SDK, import errors
- **Config Validation** — OTG schema violations, malformed configs
- **Deployment** — Docker/Containerlab failures, infrastructure issues
- **Licensing** — Cost calculations, license tier recommendations
- **Data Handoff** — Agent-to-agent data format/structure issues
- **CLI/API** — Command invocation, authentication, rate limits
- **Type Hints** — Python type annotation issues
- **State Management** — Inconsistent state between agents, race conditions
- **Error Handling** — Silent failures, unclear error messages
- **Documentation** — Missing context, unclear instructions

---

## Quick Reference by Agent

### 🔵 ixia-c-deployment-agent
*Infrastructure provisioning — Docker Compose, Containerlab, veth setup*

- [Port Alignment Issues]
- [Docker compose failures]
- [Containerlab topology issues]

### 🟢 otg-config-generator-agent
*Natural language → OTG config translation*

- [Config schema violations]
- [Port count mismatches]
- [Protocol support issues]

### 🟣 snappi-script-generator-agent
*OTG config → executable Python script*

- [Python syntax errors]
- [Snappi SDK import issues]
- [Controller connection timeouts]

### 🟠 keng-licensing-agent
*Licensing recommendations & cost estimation*

- [Cost calculation errors]
- [License tier mismatches]

---

## How to Use This File

1. **At session start:** Scan this file for known issues that might apply to current work
2. **During development:** Check relevant category before starting new agent logic
3. **On error:** Search by symptom; implement documented solution
4. **After fix:** Add entry with full context so future agents learn from it
5. **In code comments:** Reference issue by section (e.g., "See fixes.md: Port Alignment Issues")

---

## Template for New Entries

```
### [Category] [Short Issue Title]
**Date:** 2026-03-21
**Agent:** [Agent name or "General"]
**Symptom:** [What failed / what the user saw]
**Root Cause:** [Why this happened]
**Solution:** [Code change / config change / logic fix]
**Prevention:** [How to avoid this next time]
**Status:** ✅ Fixed

Example code/config that failed:
\`\`\`python
# Before
...code that failed...
\`\`\`

Fixed version:
\`\`\`python
# After
...corrected code...
\`\`\`
```

---

## Statistics

| Category | Count | Status |
|----------|-------|--------|
| Port Alignment | 0 | — |
| Script Generation | 0 | — |
| Config Validation | 0 | — |
| Deployment | 0 | — |
| Licensing | 0 | — |
| Data Handoff | 0 | — |
| Other | 0 | — |

**Total Issues:** 0 | **Fixed:** 0 | **Monitoring:** 0

---

## Last Updated
2026-03-21 (created)
