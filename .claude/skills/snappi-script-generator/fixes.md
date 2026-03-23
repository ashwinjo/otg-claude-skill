# fixes.md — snappi-script-generator

Known failure patterns for this skill. Read this before generating any output.
New entries go at the bottom. Duplicate cross-cutting fixes here — skills are self-contained.

---

### [Script Generation] Fabricated Metrics API
**Wrong:** `req.flow.state = snappi.MetricsRequest.FlowMetricState.any`
**Right:** `req.choice = req.FLOW`
**Why:** `MetricsRequest.FlowMetricState` does not exist; flow metrics are requested via `req.choice`

```python
# WRONG
req = snappi.MetricsRequest()
req.flow.state = snappi.MetricsRequest.FlowMetricState.any

# RIGHT
req = api.metrics_request()
req.choice = req.FLOW
metrics = api.get_metrics(req)
```

---

### [Script Generation] Wrong ISIS Field Names
**Wrong:** `ethernet_name`, `isis.routers.router()`, `hello_interval`, `dead_interval`
**Right:** `eth_name`, flat `v4_routes` on IsisRouter, `network_type`, `level_type`
**Why:** ISIS patterns were modelled on IOS-XR, not the OTG schema — all field names differ

---

### [Script Generation] VLAN: IPv4 Must Be on Ethernet, Not VLAN
**Wrong:** `vlan.ipv4_addresses.ipv4()` — placing IPv4 under the VLAN object
**Right:** IPv4 addresses always on the Ethernet interface; VLAN only has `name`, `id`, `priority`, `tpid`
**Why:** OTG uses a flat model — VLAN tags the Ethernet frame, it does not create a sub-interface with its own IP

```python
# WRONG
vlan = e.vlans.vlan()
addr = vlan.ipv4_addresses.ipv4()

# RIGHT
vlan = e.vlans.vlan()
vlan.name = "vlan100"
vlan.id = 100
addr = e.ipv4_addresses.ipv4()   # IPv4 stays on Ethernet
```

---

### [Script Generation] QinQ: Use Flat VLAN Array, Not Nested
**Wrong:** `outer.vlans.vlan()` — nesting VLANs inside VLANs
**Right:** Two entries in the flat `e.vlans` array: `[0]` = outer, `[1]` = inner
**Why:** OTG VLAN model is a flat ordered array, not a hierarchy

```python
# WRONG
outer = e.vlans.vlan()
inner = outer.vlans.vlan()

# RIGHT
outer = e.vlans.vlan()   # index 0 — outer VLAN (S-Tag)
inner = e.vlans.vlan()   # index 1 — inner VLAN (C-Tag)
```

---

### [CLI/API] ControlState: Use .choice + .all.state, Not .Protocol Class Attribute
**Wrong:** `cs.protocol.state = snappi.ControlState.Protocol.start`
**Right:** `cs.protocol.choice = cs.protocol.ALL` then `cs.protocol.all.state = cs.protocol.all.START`
**Why:** `snappi.ControlState.Protocol` is not a class attribute — AttributeError at runtime

```python
# WRONG
cs = snappi.ControlState()
cs.protocol.state = snappi.ControlState.Protocol.start

# RIGHT
cs = snappi.ControlState()
cs.protocol.choice = cs.protocol.ALL
cs.protocol.all.state = cs.protocol.all.START   # or .STOP
api.set_control_state(cs)
```

---

### [Script Generation] BGP session_state Value is "up", Not "established"
**Wrong:** `if m.session_state == "established"`
**Right:** `if m.session_state in ("up", "established")`
**Why:** ixia-c returns `"up"` — checking only `"established"` causes the convergence poll to loop forever

```python
# WRONG
if m.session_state == "established":
    bgp_up += 1

# RIGHT
if m.session_state in ("up", "established"):
    bgp_up += 1
```

---

### [Config Validation] BGP as_number is the Local AS, Not Remote AS
**Wrong:** Setting `as_number: 65002` on the device whose local AS is 65001
**Right:** `as_number` = the AS this device advertises in its BGP OPEN message (its own local AS)
**Why:** Each side sends its own AS in OPEN; setting the wrong value triggers a NOTIFICATION and the session never establishes

```python
# WRONG — device1 (local AS 65001) sends peer's AS in OPEN
peer.as_number = 65002

# RIGHT
peer.as_number = 65001   # local AS of THIS device
```

---

### [Script Generation] Flow Duration: fixed_seconds Crashes keng-controller
**Wrong:** `"duration": { "choice": "fixed_seconds", "fixed_seconds": { "seconds": 10 } }`
**Right:** Set `"duration": { "choice": "continuous" }` in OTG config; stop traffic via `api.set_control_state()` after desired duration
**Why:** keng-controller v1.48.0-5 crash-restarts when fixed-duration flows self-terminate, dropping the API connection mid-test

---

### [API Misuse] Config.loads() Does Not Exist — Use .deserialize()
**Wrong:** `cfg.loads(json_string)`
**Right:** `cfg.deserialize(json_string)` to load; `cfg.serialize()` to export
**Why:** `loads` is Python stdlib (json module), not a snappi.Config method — AttributeError at runtime

```python
# WRONG
cfg = snappi.Config()
cfg.loads(otg_json_string)

# RIGHT
cfg = snappi.Config()
cfg.deserialize(otg_json_string)
api.set_config(cfg)

# Export config to JSON string
json_output = cfg.serialize()
```

---

### [Config Validation] ixia-c-one: latency and loss Metric Fields Not Supported
**Wrong:** Including `metrics.latency` or `metrics.loss` in flow config for ixia-c-one deployments
**Right:** Use only `metrics.enable = True` for ixia-c-one; collect port-level stats instead
**Why:** ixia-c-one (all-in-one bundle) does NOT support flow-level latency or loss — config push is rejected

```python
# WRONG for ixia-c-one
flow.metrics.enable = True
flow.metrics.loss = True
flow.metrics.latency.enable = True
flow.metrics.latency.mode = flow.metrics.latency.STORE_FORWARD

# RIGHT for ixia-c-one
flow.metrics.enable = True   # basic frame counters only
```

---

### [Deployment] docker cp config.yaml: Always chmod 644 After Copy
**Wrong:** `docker cp config.yaml keng-controller:/home/ixia-c/controller/config/` without follow-up chmod
**Right:** Add `sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml` immediately after
**Why:** `docker cp` sets mode 600 owned by root; the controller process runs as non-root and cannot read the file, returning HTTP 500 `permission denied`

```bash
# WRONG
docker cp config.yaml keng-controller:/home/ixia-c/controller/config/config.yaml

# RIGHT
docker cp config.yaml keng-controller:/home/ixia-c/controller/config/config.yaml
sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml
```

---

### [Deployment] Containerlab: Controller IP Is Not localhost
**Wrong:** Hardcoding `https://localhost:8443` as the controller URL in scripts targeting Containerlab deployments
**Right:** Discover the container IP after deploy and pass it to the script
**Why:** ixia-c-one runs on Containerlab's internal Docker bridge network, not on the host; `localhost` resolves to the host machine

```bash
# Discover IP after containerlab deploy
IXIA_IP=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' clab-<topo-name>-ixia-c)
# Use: https://${IXIA_IP}:8443
```
