# fixes.md — otg-config-generator

Known failure patterns for this skill. Read this before generating any output.
New entries go at the bottom. Duplicate cross-cutting fixes here — skills are self-contained.

---

### [Config Validation] Wrong Device Field Names
**Wrong:** `device_eth`, `container_name`, `asn`, `neighbors`, `ipv4_unicast.sendunicast`
**Right:** `ethernets` (array on Device), no `container_name` field, `as_number` on V4Peer, `bgp.ipv4_interfaces[].peers[]` hierarchy
**Why:** OTG OpenAPI schema v1.49.0 defines exact field names — any deviation is silently rejected or causes a schema error

```json
// WRONG
{
  "device_eth": {...},
  "container_name": "device1",
  "bgp": [{ "asn": 65001, "neighbors": [...] }]
}

// RIGHT
{
  "ethernets": [{ "name": "eth1", ... }],
  "bgp": {
    "router_id": "1.1.1.1",
    "ipv4_interfaces": [{
      "ipv4_name": "ipv4_1",
      "peers": [{ "name": "peer1", "peer_address": "...", "as_type": "ebgp", "as_number": 65001 }]
    }]
  }
}
```

---

### [Config Validation] Missing Required BGP Fields
**Wrong:** Omitting `as_type`, `name`, `ipv4_name` on BGP objects
**Right:** Every `V4Peer` needs `name`, `peer_address`, `as_type`, `as_number`; every `V4Interface` needs `ipv4_name`
**Why:** These are required fields in the OTG schema — missing any one causes config push to fail

---

### [Config Validation] BGP as_number is the Local AS, Not Remote AS
**Wrong:** Setting `as_number: 65002` on the device whose local AS is 65001
**Right:** `as_number` = the AS this device advertises in its BGP OPEN message (its own local AS)
**Why:** Each side sends its own AS in OPEN; setting the wrong value triggers a NOTIFICATION and the session never establishes

```json
// WRONG — device1 (local AS 65001) has as_number set to peer's AS
{ "peer_address": "10.0.0.2", "as_type": "ebgp", "as_number": 65002 }

// RIGHT
{ "peer_address": "10.0.0.2", "as_type": "ebgp", "as_number": 65001 }
```

---

### [Config Validation] BGP B2B: Missing passive_mode Causes Session Flap
**Wrong:** Both emulated devices in a back-to-back (veth) topology without `passive_mode`
**Right:** Set `"advanced": { "passive_mode": true }` on one side so only the active side initiates TCP
**Why:** Both sides attempting simultaneous TCP open triggers BGP collision resolution, sends NOTIFICATION, session flaps

```json
// RIGHT — device2 is passive side
{
  "peer_address": "10.0.0.1",
  "as_type": "ebgp",
  "as_number": 65002,
  "advanced": { "passive_mode": true }
}
```

---

### [Config Validation] Flow Duration: fixed_seconds Crashes keng-controller
**Wrong:** `"duration": { "choice": "fixed_seconds", "fixed_seconds": { "seconds": 10 } }`
**Right:** `"duration": { "choice": "continuous" }` — stop traffic programmatically from the test script
**Why:** keng-controller v1.48.0-5 crash-restarts when fixed-duration flows self-terminate, dropping the API connection mid-test

---

### [Config Validation] ixia-c-one: latency and loss Metric Fields Not Supported
**Wrong:** Including `"metrics": { "latency": {...}, "loss": true }` in flow config for ixia-c-one deployments
**Right:** Use only `"metrics": { "enable": true }` (basic frame counters) for ixia-c-one; collect port-level stats instead
**Why:** ixia-c-one (all-in-one bundle) does NOT support flow-level latency or loss metrics — config push is rejected with an explicit error

```json
// WRONG for ixia-c-one
"metrics": { "enable": true, "latency": { "enable": true, "mode": "store_forward" }, "loss": true }

// RIGHT for ixia-c-one
"metrics": { "enable": true }
```
