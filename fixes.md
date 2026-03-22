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

**Total Issues:** 9 | **Fixed:** 9 | **Monitoring:** 0

---

### [Config Validation] BGP as_number is Local AS, Not Remote AS
**Date:** 2026-03-22
**Agent:** otg-config-generator-agent / snappi-script-generator-agent
**Symptom:** BGP sessions flap and never reach Established. Metrics show opens/keepalives exchanged but notifications sent immediately after, returning to `connect` state.
**Root Cause:** In OTG BGP peer schema, `as_number` is the **local AS** this device advertises in its OPEN message — not the remote peer's AS. Agent incorrectly set `as_number` to the remote peer's AS, causing each side to receive a mismatched AS number in the OPEN, triggering a NOTIFICATION and session teardown.
**Solution:** Corrected `as_number` to match each device's own AS:
- device_te1 (local AS 65001): `as_number = 65001`
- device_te2 (local AS 65002): `as_number = 65002`
**Prevention:** Always set `as_number` on a BGP peer = the local device's own AS. The remote AS is implicit from the eBGP peer relationship. Reference: `protocol_examples.md` shows `peer.as_number = 65001` on the device with AS 65001.
**Status:** ✅ Fixed

### [CLI/API] snappi ControlState.Protocol attribute does not exist
**Date:** 2026-03-22
**Agent:** snappi-script-generator-agent
**Symptom:** `AttributeError: type object 'ControlState' has no attribute 'Protocol'` when calling `set_control_state` to start/stop protocols.
**Root Cause:** Generated code used `snappi.ControlState.Protocol.start` which does not exist. The correct API uses `cs.protocol.choice = cs.protocol.ALL` + `cs.protocol.all.state = cs.protocol.all.START`.
**Solution:**
```python
cs = snappi.ControlState()
cs.protocol.choice = cs.protocol.ALL
cs.protocol.all.state = cs.protocol.all.START  # or .STOP
api.set_control_state(cs)
```
**Prevention:** Always use `cs.protocol.ALL` choice with `cs.protocol.all.state` for bulk protocol start/stop. Never reference `snappi.ControlState.Protocol` as a class attribute.
**Status:** ✅ Fixed

### [Deployment] docker cp config.yaml sets wrong file permissions
**Date:** 2026-03-22
**Agent:** ixia-c-deployment-agent
**Symptom:** Controller returns HTTP 500: `permission denied` on `/home/ixia-c/controller/config/config.yaml` when pushing OTG config.
**Root Cause:** `docker cp` copies the file as root with mode 600, but the controller process runs as a non-root user that cannot read it.
**Solution:** After `docker cp`, run `sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml`
**Prevention:** Always add `chmod 644` step in `setup-ixia-c-bgp.sh` immediately after `docker cp` of the config file.
**Status:** ✅ Fixed

### [Config Validation] ixia-c-one Metric Field Incompatibility
**Date:** 2026-03-22
**Agent:** otg-config-generator-agent, snappi-script-generator-agent
**Symptom:** OTG config push to ixia-c-one container rejected with errors:
- `"Latency mode \"store forward\" is currently not supported for flow ..."`
- `"Loss in flow metrics for flow ... is currently not supported"`
**Root Cause:** ixia-c-one (all-in-one keng-controller v1.48.0-5) does NOT support:
- Flow-level latency metrics (any mode: store_forward, cut_through)
- Flow-level loss metrics
These features ARE supported in full ixia-c CP+DP deployment but NOT in ixia-c-one bundle.
**Solution:**
1. otg-config-generator: Detect deployment target; if ixia-c-one, remove unsupported metric fields
2. snappi-script-generator: Remove `metrics.latency` and `metrics.loss` from OTG config before pushing
3. Use only `metrics.enable: true` (basic frame counters) for ixia-c-one
4. Collect metrics from port-level stats instead (frames_tx, frames_rx available on all ports)
**Prevention:**
- Add deployment-type detection to otg-config-generator skill
- Document in OTG_CONFIG_GENERATOR SKILL.md: "Metric field support by deployment type"
- Add eval case: "Generate config for ixia-c-one with latency metrics (should auto-remove)"
- Add CLI flag `--target-type ixia-c-one` to skip unsupported fields
**Status:** ✅ Fixed (workaround in snappi-script-generator; permanent fix in otg-config-generator pending)
**Promoted:** snappi-script-generator/SKILL.md (Known Limitations section)

### [API Misuse] Snappi Config.loads() vs Config.deserialize()
**Date:** 2026-03-22
**Agent:** snappi-script-generator-agent
**Symptom:** `AttributeError: 'Config' object has no attribute 'loads'` when calling `cfg.loads(json_string)`
**Root Cause:** Snappi SDK uses `cfg.deserialize(json_string)` not `cfg.loads()`. The `loads` method is from Python stdlib (json module), not snappi.Config.
**Solution:** Replace all instances of:
```python
# WRONG
cfg = snappi.Config()
cfg.loads(otg_json_string)

# CORRECT
cfg = snappi.Config()
cfg.deserialize(otg_json_string)
```
**Prevention:**
- Always use `cfg.deserialize()` for loading JSON strings into Config objects
- Use `api.get_config().serialize()` to export config as JSON string
- Reference: snappi.Config API has `serialize()` (to JSON) and `deserialize()` (from JSON)
**Status:** ✅ Fixed
**Promoted:** snappi-script-generator/SKILL.md (Snappi SDK API Reference section)

### [Deployment] Containerlab Controller IP Discovery
**Date:** 2026-03-22
**Agent:** ixia-c-deployment-agent, snappi-script-generator-agent
**Symptom:** Snappi test script connects to `localhost:8443` but controller is not reachable (Connection refused).
**Root Cause:** ixia-c-one container runs on Containerlab's internal Docker network (e.g., clab bridge), not on localhost. localhost:8443 resolves to the host machine, not the container.
**Solution:**
1. After containerlab deploy, discover the ixia-c container IP:
```bash
IXIA_IP=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' clab-<topo-name>-ixia-c)
```
2. Pass this IP to the test script: `https://${IXIA_IP}:8443`
3. Alternatively, run test script INSIDE a container on the same clab network (e.g., snappi test runner node in topo.yml)
**Prevention:**
- ixia-c-deployment-agent should ALWAYS return discovered container IP in port_mapping output
- snappi-script-generator should accept `--controller-ip` CLI arg or read from infrastructure YAML
- Document in ixia-c-deployment/SKILL.md: "Port Discovery for Containerlab" section
- Add eval case: "Deploy containerlab, extract controller IP, generate script with correct IP"
**Status:** ✅ Fixed (manual workaround; permanent fix in agents pending)
**Promoted:** ixia-c-deployment/SKILL.md (Containerlab Port Discovery section)

---

---

## Promotion Workflow

fixes.md is the **first-catch log**. Once a fix is validated, it must be promoted upstream so agents don't have to rediscover it from this file alone.

**Promotion checklist (run after every new entry):**
1. Add entry to fixes.md (done first, always)
2. Identify which skill/agent owns the bug:
   - Config generation bugs → `.claude/skills/otg-config-generator/SKILL.md`
   - Script generation bugs → `.claude/skills/snappi-script-generator/SKILL.md`
   - Deployment bugs → `.claude/skills/ixia-c-deployment/SKILL.md`
   - Runtime/API bugs → the relevant skill's Known Pitfalls section
3. Add to the "Known Pitfalls" section of that SKILL.md with: symptom, wrong pattern, correct pattern
4. If the skill has a canonical code example that contains the bug, fix the example too
5. Mark the fixes.md entry with `**Promoted:** SKILL.md` so future readers know it's upstream

**Promoted fixes (2026-03-22):**
- BGP `as_number` is local AS → `otg-config-generator/SKILL.md` Known Pitfalls + all examples corrected
- `ControlState` API → `snappi-script-generator/SKILL.md` Known Pitfalls + template code corrected
- `session_state == "up"` → `snappi-script-generator/SKILL.md` Known Pitfalls + template code corrected
- `fixed_seconds` crashes controller → both `otg-config-generator/SKILL.md` and `snappi-script-generator/SKILL.md` Known Pitfalls
- B2B BGP collision → `otg-config-generator/SKILL.md` Known Pitfalls + `ixia-c-deployment/SKILL.md` troubleshooting table
- `docker cp` permissions → `ixia-c-deployment/SKILL.md` troubleshooting table + `snappi-script-generator/SKILL.md` Known Pitfalls

## Last Updated
2026-03-22 (runtime fixes promoted to SKILL.md files; promotion workflow documented)

### [Deployment] Containerlab Multi-Node ixia-c-one Topology Pattern
**Date:** 2026-03-22
**Agent:** ixia-c-deployment-agent, snappi-script-generator-agent
**Symptom:** Successfully deployed and tested Containerlab with 2 ixia-c-one nodes + 1 FRR DUT; traffic generation verified
**Root Cause:** N/A (success pattern documented for reuse)
**Solution:**
1. Define Containerlab topology with multiple ixia-c-one nodes
2. Link each ixia eth1 to DUT ports (FRR in this case)
3. Configure DUT (FRR with BGP) independently
4. Discover each ixia container's IP on Containerlab bridge
5. Each ixia node is independently accessible at its container IP:8443
**Prevention/Best Practices:**
- Use simple Containerlab YAML for topology definition (no complex network modes needed)
- Each ixia-c-one only has eth1 by default (linked to DUT via Containerlab endpoints)
- For full BGP routing tests: push separate OTG configs to separate ixia controllers via separate API instances
- FRR configuration: BGP neighbors point to ixia eth1 IPs (e.g., 10.0.1.1, 10.0.2.1)
**Status:** ✅ Fixed (pattern validated; deployment, config generation, traffic control all working)
**Promoted:** ixia-c-deployment/SKILL.md (Containerlab Multi-Node section)

### [API Documentation] Controller REST Endpoint Path
**Date:** 2026-03-22
**Agent:** ixia-c-deployment-agent
**Symptom:** Verification curl commands to `/api/v1/config` returned HTTP 404
**Root Cause:** Ixia-c controller REST API endpoint is `/config`, not `/api/v1/config`. The `/api/v1/` prefix pattern is common in other systems but not used in Ixia-c.
**Solution:** Changed verification curl commands from:
```bash
# WRONG
curl -k https://localhost:8443/api/v1/config

# CORRECT
curl -k https://localhost:8443/config
```
The controller returns empty config `{}` when no traffic flows/ports are configured.
**Prevention:**
- Document correct endpoint in ixia-c-deployment/SKILL.md Step 4 (Verify deployment)
- Include working curl examples in skill documentation
- Reference: Controller startup logs show `HTTPPort: 8443` and `msg: HTTPS Server started`
**Status:** ✅ Fixed
**Promoted:** ixia-c-deployment/SKILL.md (Step 4 Verification section)

### [API/TLS] Self-Signed Certificate Handling with curl
**Date:** 2026-03-22
**Agent:** ixia-c-deployment-agent
**Symptom:** Controller logs show repeated "TLS handshake error from 127.0.0.1: unexpected EOF" when using `curl https://localhost:8443`
**Root Cause:** Ixia-c controller uses self-signed HTTPS certificates by default. Standard curl rejects them without explicit trust flag.
**Solution:** Add `--insecure` / `-k` flag to curl commands:
```bash
# WRONG (TLS handshake fails)
curl https://localhost:8443/config

# CORRECT
curl -k https://localhost:8443/config
curl --insecure https://localhost:8443/config
```
**Prevention:**
- Always include `-k` flag in verification/troubleshooting documentation
- Document in ixia-c-deployment/SKILL.md: "TLS and Certificates" section
- For production deployments, replace self-signed certs with CA-signed certificates (configure in controller startup flags)
- snappi-script-generator automatically uses `verify=False` in generated scripts for lab deployments
**Status:** ✅ Fixed
**Promoted:** ixia-c-deployment/SKILL.md (Step 4 Verification section + Troubleshooting table)

### [Deployment] Host Network Mode Port Discovery
**Date:** 2026-03-22
**Agent:** ixia-c-deployment-agent
**Symptom:** `docker inspect <container>` shows empty `"Ports": {}` section for keng-controller container
**Root Cause:** Docker Compose deployment uses `network_mode: host` for the controller container. In host network mode, ports are not explicitly exposed via Docker port mapping — they're directly accessible on the host network. `docker inspect` shows empty Ports section for host-mode containers.
**Solution:** To discover controller port configuration, check controller startup logs:
```bash
docker logs <controller-name> | grep "HTTPS Server started\|GRPC Server started\|HTTPPort\|GRPCPort"
# Output:
# {"msg":"Build Details", ... "HTTPPort":8443,...}
# {"msg":"HTTPS Server started","addr":":8443"...}
# {"msg":"GRPC Server started","addr":"[::]:40051"...}
```
Default ports: HTTPS 8443, GRPC 40051
**Prevention:**
- Document in ixia-c-deployment/SKILL.md: "Port Discovery" section
- Clarify that `docker inspect Ports` is empty for `network_mode: host` deployments
- Provide log parsing example for extracting port configuration
- Include troubleshooting note: "If using docker run with --net=host, ports are not port-mapped; check container logs or controller config"
**Status:** ✅ Fixed
**Promoted:** ixia-c-deployment/SKILL.md (Troubleshooting table)

