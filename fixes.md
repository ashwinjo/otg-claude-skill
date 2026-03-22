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

### [Config Validation] OTG Config Generator — Wrong Device Field Names
**Date:** 2026-03-21
**Agent:** otg-config-generator-agent
**Symptom:** Generated configs use `device_eth`, `container_name`, `bgp` as array, `asn`, `neighbors`, `ipv4_unicast.sendunicast` — all invalid per OTG OpenAPI schema
**Root Cause:** SKILL.md templates were written from memory/hallucination, not validated against openapi.yaml (v1.49.0)
**Solution:** Rewrote SKILL.md with correct field names:
- `device_eth` → `ethernets` (array)
- Removed `container_name` (does not exist)
- `bgp` is a single object, NOT an array
- Removed `asn` → AS is `as_number` on each `Bgp.V4Peer`
- Removed `ipv4_unicast.sendunicast` (does not exist)
- `neighbors` → `bgp.ipv4_interfaces[].peers[]`
- Added required `as_type` (ibgp/ebgp) on every peer
- Added required `ipv4_name` on `Bgp.V4Interface`
- Fixed flow template: `tx_port`/`rx_ports` → `tx_rx` with choice pattern
**Prevention:** Always cross-reference openapi.yaml when writing OTG config templates. Added "Schema Quick Reference" table at top of SKILL.md with correct vs wrong field names.
**Status:** ✅ Fixed

### [Config Validation] OTG Config Generator — Missing Required BGP Fields
**Date:** 2026-03-21
**Agent:** otg-config-generator-agent
**Symptom:** Generated BGP configs missing `as_type`, `name` on peers, `ipv4_name` on interfaces — all required by schema
**Root Cause:** BGP hierarchy was flattened incorrectly; required fields not documented in skill
**Solution:** Added full BGP hierarchy diagram to SKILL.md showing Device.bgp → ipv4_interfaces[] → peers[] with all required fields marked
**Prevention:** SKILL.md now has explicit "Required Fields" annotations in schema reference table
**Status:** ✅ Fixed

### [Script Generation] Snappi Script Generator — Fabricated Metrics API
**Date:** 2026-03-21
**Agent:** snappi-script-generator-agent
**Symptom:** `collect_metrics()` used `req.flow.state = snappi.MetricsRequest.FlowMetricState.any` which doesn't exist
**Root Cause:** API pattern hallucinated instead of referencing github_snippets.md
**Solution:** Changed to correct pattern: `req.choice = req.FLOW`
**Prevention:** Always reference github_snippets.md for Snappi API patterns
**Status:** ✅ Fixed

### [Script Generation] Protocol Examples — Wrong ISIS Field Names
**Date:** 2026-03-21
**Agent:** snappi-script-generator-agent
**Symptom:** ISIS example used `ethernet_name` (should be `eth_name`), `isis.routers.router()` (doesn't exist), `hello_interval`/`dead_interval` (not on Isis.Interface)
**Root Cause:** ISIS patterns fabricated from IOS-XR mental model, not OTG schema
**Solution:** Rewrote ISIS example with correct fields: `eth_name`, `system_id`, flat `v4_routes` on IsisRouter, `network_type`, `level_type`
**Prevention:** Validate all protocol examples against openapi.yaml
**Status:** ✅ Fixed

### [Script Generation] Protocol Examples — VLAN IPv4 Nesting Error
**Date:** 2026-03-21
**Agent:** snappi-script-generator-agent
**Symptom:** VLAN example placed `ipv4_addresses` under VLAN object (`vlan.ipv4_addresses.ipv4()`). Schema puts IPv4 on Ethernet, not VLAN.
**Root Cause:** Assumed VLAN sub-interface model (like IOS). OTG uses flat model: VLAN tags Ethernet, IPv4 stays on Ethernet.
**Solution:** Moved IPv4 back to Ethernet interface. Added key rules note explaining VLAN only has `name`, `id`, `priority`, `tpid`.
**Prevention:** Document: "IPv4 addresses always on Ethernet, never nested under VLAN"
**Status:** ✅ Fixed

### [Script Generation] Protocol Examples — QinQ Nested VLAN Error
**Date:** 2026-03-21
**Agent:** snappi-script-generator-agent
**Symptom:** QinQ example used `outer.vlans.vlan()` (nested VLANs inside VLANs). Schema uses flat array.
**Root Cause:** Assumed nested VLAN model. OTG uses flat `e.vlans` array with outer first, inner second.
**Solution:** Changed to flat array: `e.vlans.vlan()[0]` (outer) and `e.vlans.vlan()[1]` (inner)
**Prevention:** Document: "QinQ = two flat entries in vlans array, NOT nested"
**Status:** ✅ Fixed

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
| Script Generation | 4 | ✅ All Fixed |
| Config Validation | 2 | ✅ All Fixed |
| Deployment | 0 | — |
| Licensing | 0 | — |
| Data Handoff | 0 | — |
| Other | 0 | — |

**Total Issues:** 6 | **Fixed:** 6 | **Monitoring:** 0

---

## Last Updated
2026-03-21 (schema audit — 6 issues fixed across otg-config-generator and snappi-script-generator)
