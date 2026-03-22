---
name: otg-config-generator
description: |
  Generate Open Traffic Generator (OTG) configurations from natural language intent.

  Use this skill whenever the user wants to:
  - Create OTG test configurations from a description of what they want to test
  - Generate traffic generator setup for network testing scenarios
  - Build configurations for emulated devices, traffic flows, and protocol testing
  - Create BGP, ISIS, LACP, LLDP, or other protocol configurations
  - Set up test ports, LAGs, VLANs, IPv4/IPv6 addressing, and traffic flows

  The skill translates user intent into structured, ready-to-deploy OTG JSON configurations.
compatibility: References openapi.yaml at the project root for schema validation (optional)
---

# OTG Configuration Generator

Generate valid Open Traffic Generator (OTG) JSON configurations from natural language test scenarios.

## How It Works

You receive a test scenario description from the user and produce a complete OTG configuration object (Config schema) that:

1. **Parses the scenario** — Extract key requirements: test ports, emulated devices, protocols, traffic flows, metrics
2. **Maps to OTG schema** — Translate requirements to OpenAPI-compliant Config objects
3. **Validates completeness** — Ensure all required fields are present, types are correct, references resolve
4. **Outputs JSON** — Return a production-ready configuration object

## Schema Quick Reference (Required Fields)

Before generating any config, internalize these **exact** field names from the OTG OpenAPI spec (v1.49.0):

### Critical Field Name Rules

| Object | Correct Field | WRONG (never use) | Type |
|--------|--------------|-------------------|------|
| Device | `ethernets` | ~~device_eth~~, ~~ethernet~~ | array of `Device.Ethernet` |
| Device | `bgp` | — | **single object** (`Device.BgpRouter`), NOT an array |
| Device | `isis` | — | **single object** (`Device.IsisRouter`), NOT an array |
| Device | `name` | ~~container_name~~ | string (required, globally unique) |
| Device | (no `container_name`) | ~~container_name~~ | field does NOT exist |
| BgpRouter | `router_id` | — | string (ipv4, required) |
| BgpRouter | `ipv4_interfaces` | ~~neighbors~~, ~~peers~~ | array of `Bgp.V4Interface` |
| BgpRouter | `ipv6_interfaces` | — | array of `Bgp.V6Interface` |
| Bgp.V4Interface | `ipv4_name` | — | string (required, refs `Device.Ipv4.name`) |
| Bgp.V4Interface | `peers` | ~~neighbors~~ | array of `Bgp.V4Peer` |
| Bgp.V4Peer | `as_type` | — | string (required: `"ibgp"` or `"ebgp"`) |
| Bgp.V4Peer | `as_number` | ~~asn~~, ~~as_num~~ | integer (required) |
| Bgp.V4Peer | `peer_address` | — | string (ipv4, required) |
| Bgp.V4Peer | `name` | — | string (required, globally unique) |
| Flow | `tx_rx` | ~~tx_port~~, ~~rx_ports~~ | object (`Flow.TxRx`, required) |
| Flow.Port | `tx_name` | ~~tx_port~~ | string (required) |
| Flow.Port | `rx_names` | ~~rx_ports~~ | array of strings |

### BGP Hierarchy (Correct Structure)

```
Device.bgp                          ← single object (NOT an array)
  ├── router_id: "10.0.0.1"        ← required
  ├── ipv4_interfaces: [            ← array of Bgp.V4Interface
  │     {
  │       ipv4_name: "ipv4_1"      ← required, references Device.Ipv4.name
  │       peers: [                  ← array of Bgp.V4Peer
  │         {
  │           name: "peer1"        ← required, globally unique
  │           peer_address: "..."  ← required
  │           as_type: "ebgp"      ← required (ibgp/ebgp)
  │           as_number: 65002     ← required
  │           v4_routes: [...]     ← optional route advertisements
  │         }
  │       ]
  │     }
  │   ]
  └── ipv6_interfaces: [...]       ← array of Bgp.V6Interface (same pattern)
```

## Workflow

### Step 1: Parse the Intent

When given a test scenario, identify:

- **Test Ports**: How many? What names? Layer 1 settings needed?
- **Emulated Devices**: How many devices? Which ports do they connect to? Standalone or LAG?
- **Addressing**: IPv4? IPv6? DHCP? Static? Gateways?
- **Protocols**: BGP? ISIS? LACP? LLDP? Any specific AS numbers, router IDs, timers?
- **Traffic Flows**: Source/destination? Port-to-port or device-to-device? Packet rates/size? Protocols (L2-4)?
- **Metrics**: What statistics to collect? Port stats? Per-flow? Packet capture?
- **Advanced Features**: VLANs? LAGs? Multiple interfaces? Stateful flows?

### Step 2: Map to OTG Schema

Use these patterns from the OpenAPI spec:

**Test Port** — Minimal config:
```json
{
  "name": "port1",
  "location": "<location-string>"
}
```

**Emulated Device** — Typical structure (with BGP):
```json
{
  "name": "device1",
  "ethernets": [
    {
      "name": "eth1",
      "connection": {
        "choice": "port_name",
        "port_name": "port1"
      },
      "mac": "00:11:22:33:44:55",
      "ipv4_addresses": [
        {
          "name": "ipv4_1",
          "address": "10.0.0.1",
          "prefix": 24,
          "gateway": "10.0.0.254"
        }
      ]
    }
  ],
  "bgp": {
    "router_id": "10.0.0.1",
    "ipv4_interfaces": [
      {
        "ipv4_name": "ipv4_1",
        "peers": [
          {
            "name": "bgp_peer_1",
            "peer_address": "10.0.0.2",
            "as_type": "ebgp",
            "as_number": 65002
          }
        ]
      }
    ]
  }
}
```

Key rules:
- `ethernets` is an **array** (plural)
- `bgp` is a **single object** (NOT an array)
- There is NO `container_name` field — use `name` only
- `ipv4_name` in `Bgp.V4Interface` MUST match a `Device.Ipv4.name` (e.g., `"ipv4_1"`)
- `as_type` is **required** on every peer: `"ebgp"` (different AS) or `"ibgp"` (same AS)

**Traffic Flow** — Port-based flow:
```json
{
  "name": "flow1",
  "tx_rx": {
    "choice": "port",
    "port": {
      "tx_name": "port1",
      "rx_names": ["port2"]
    }
  },
  "packet": [
    {
      "choice": "ethernet",
      "ethernet": {
        "dst": {
          "choice": "value",
          "value": "00:00:00:00:00:01"
        },
        "src": {
          "choice": "value",
          "value": "00:00:00:00:00:02"
        }
      }
    }
  ],
  "rate": {
    "choice": "pps",
    "pps": 1000
  },
  "duration": {
    "choice": "continuous"
  }
}
```

**Traffic Flow** — Device-based flow (for routed traffic via BGP routes):
```json
{
  "name": "flow1",
  "tx_rx": {
    "choice": "device",
    "device": {
      "tx_names": ["routes_v4_device1"],
      "rx_names": ["routes_v4_device2"],
      "mode": "mesh"
    }
  },
  "packet": [
    {"choice": "ethernet", "ethernet": {}},
    {"choice": "ipv4", "ipv4": {}}
  ],
  "rate": {"choice": "pps", "pps": 1000},
  "duration": {"choice": "continuous"}
}
```

Key flow rules:
- Always use `tx_rx` with `choice` pattern — NEVER use `tx_port`/`rx_ports`
- For port-based: `tx_rx.choice: "port"` → `tx_rx.port.tx_name` / `tx_rx.port.rx_names`
- For device-based: `tx_rx.choice: "device"` → `tx_rx.device.tx_names` / `tx_rx.device.rx_names`
- `name` and `tx_rx` are required on every flow

**BGP Peer with Route Advertisement** — Advertising prefixes:
```json
{
  "name": "bgp_peer_1",
  "peer_address": "10.0.0.2",
  "as_type": "ebgp",
  "as_number": 65002,
  "v4_routes": [
    {
      "name": "routes_v4",
      "addresses": [
        {"address": "192.168.0.0", "prefix": 24, "count": 100, "step": 1}
      ]
    }
  ]
}
```
`count` = number of prefixes, `step` = increment between prefixes (1 = 192.168.0.0/24, 192.168.1.0/24, ..., 192.168.99.0/24).
`v4_routes` is on the **peer** object (`Bgp.V4Peer`), NOT on `BgpRouter`.

**IPv6 Addressing** — Adding IPv6 to an Ethernet interface:
```json
{
  "name": "eth1",
  "connection": {"choice": "port_name", "port_name": "port1"},
  "mac": "00:11:22:33:44:55",
  "ipv4_addresses": [{"name": "ipv4_1", "address": "10.0.0.1", "prefix": 24, "gateway": "10.0.0.254"}],
  "ipv6_addresses": [{"name": "ipv6_1", "address": "2001:db8::1", "prefix": 64, "gateway": "2001:db8::fe"}]
}
```

**BGP IPv6 Peer** — For dual-stack or IPv6-only BGP:
```json
{
  "bgp": {
    "router_id": "10.0.0.1",
    "ipv4_interfaces": [
      {
        "ipv4_name": "ipv4_1",
        "peers": [
          {
            "name": "bgp_v4_peer_1",
            "peer_address": "10.0.0.2",
            "as_type": "ebgp",
            "as_number": 65002
          }
        ]
      }
    ],
    "ipv6_interfaces": [
      {
        "ipv6_name": "ipv6_1",
        "peers": [
          {
            "name": "bgp_v6_peer_1",
            "peer_address": "2001:db8::fe",
            "as_type": "ebgp",
            "as_number": 65002,
            "v6_routes": [
              {
                "name": "routes_v6",
                "addresses": [
                  {"address": "2001:db8:100::", "prefix": 48, "count": 10, "step": 1}
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Multi-hop eBGP** — When peers are not directly connected (e.g., separated by a router):
Set `as_type` to `"ebgp"`. For multi-hop scenarios the peer's IP is not the directly connected address — ensure the gateway and routing allow reachability to the peer. Note that `as_type` is **required** on every peer: use `"ebgp"` for external peers (different AS), `"ibgp"` for internal peers (same AS).

**ISIS Router** — For IS-IS protocol testing:
```json
{
  "name": "device1",
  "ethernets": [
    {
      "name": "eth1",
      "connection": {"choice": "port_name", "port_name": "port1"},
      "mac": "00:11:22:33:44:55",
      "ipv4_addresses": [
        {"name": "ipv4_1", "address": "10.0.0.1", "prefix": 24, "gateway": "10.0.0.254"}
      ]
    }
  ],
  "isis": {
    "name": "isis_router_1",
    "system_id": "640100010000",
    "interfaces": [
      {
        "eth_name": "eth1",
        "name": "isis_iface_1",
        "network_type": "point_to_point",
        "level_type": "level_2"
      }
    ]
  }
}
```

Key ISIS rules:
- `isis` is a **single object** (NOT an array)
- `system_id` is **required** (hex string, e.g., `"640100010000"`)
- `interfaces` array is **required**, each entry needs `eth_name` (refs `Device.Ethernet.name`) and `name`
- `level_type`: `"level_1"`, `"level_2"` (default), or `"level_1_2"`
- Use `ipv4_loopbacks` on Device for loopback addresses (NOT inside ethernets)

**LACP LAG** — For port aggregation:
```json
{
  "name": "lag1",
  "ports": [
    {
      "port_name": "port1",
      "ethernet": { "name": "lag_eth1" },
      "lacp": {
        "actor_port_number": 1,
        "actor_port_priority": 32768,
        "actor_activity": "active"
      }
    }
  ],
  "protocol": {
    "choice": "lacp",
    "lacp": {
      "actor_system_id": "00:00:00:00:00:01"
    }
  }
}
```

### Step 3: Validate Requirements

Before returning the config:

1. **All required fields present** — Every object has its required fields per schema
2. **Name uniqueness** — Global uniqueness for all named objects (ports, devices, flows, ethernets, ipv4 addresses, bgp peers, etc.)
3. **Reference integrity** — `ipv4_name` in BGP references existing `Device.Ipv4.name`; ethernet `connection.port_name` references existing `Port.name`
4. **Flow connectivity** — `tx_rx.port.tx_name` and `tx_rx.port.rx_names` reference existing ports/lags
5. **as_type present** — Every BGP peer has `as_type` set (`"ebgp"` or `"ibgp"`)
6. **Constraint compliance** — LAG ports (1-32), prefix lengths (valid ranges), AS numbers (uint32), etc.
7. **Protocol consistency** — BGP peers reference correct IPv4/IPv6 address names, ISIS interfaces reference correct ethernet names

### Step 4: Return Configuration

Output a complete `Config` object with these top-level fields:

```json
{
  "ports": [...],
  "lags": [...],
  "layer1": [...],
  "devices": [...],
  "flows": [...],
  "captures": [...],
  "lldp": [...],
  "options": {...}
}
```

Return the JSON configuration followed by a brief summary: number of ports, devices, protocols configured (e.g., BGP, ISIS, LACP), and flows. This helps the engineer quickly confirm the output matches their intent before deploying.

## Common Patterns

### Port-to-Port Traffic (Simple)
1 Tx port → 1 Rx port → 1 Flow (using `tx_rx.choice: "port"`)

### Device-to-Device BGP Test
- Device 1: Port1, IPv4 10.0.0.1/24, BGP AS 65001 (ebgp peer)
- Device 2: Port2, IPv4 10.0.0.2/24, BGP AS 65002 (ebgp peer)
- Flow: From Device1 routes to Device2 routes (using `tx_rx.choice: "device"`)

### LAG with LACP
- Port1 + Port2 → LAG1
- Device connected to LAG1 via `connection.choice: "lag_name"`
- LAG protocol set to `lacp`

### VLAN Tagging
VLANs are configured in `ethernets[].vlans[]` — a separate array inside the Ethernet interface, not inside `ipv4_addresses`. The IPv4 address sits on top of the VLAN-tagged interface.

```json
{
  "name": "eth1",
  "connection": {"choice": "port_name", "port_name": "port1"},
  "mac": "00:11:22:33:44:55",
  "vlans": [{"name": "vlan100", "id": 100, "priority": 0}],
  "ipv4_addresses": [{"name": "ipv4_1", "address": "10.100.0.1", "prefix": 24, "gateway": "10.100.0.254"}]
}
```

For QinQ (double-tagged), add two entries to `vlans[]` — outer VLAN first, then inner.

### Multi-Device Topology
Chain devices with interconnected Ethernet interfaces:
- Device A: eth1 (port1) + eth2 (device_b.eth1, simulated)
- Device B: eth1 (device_a.eth2, simulated) + eth2 (port2)
- Protocols run on each device independently

## Error Handling

If the user's intent is:
- **Incomplete** — Ask clarifying questions about missing details (port locations, addresses, protocol AS numbers, etc.)
- **Invalid** — Point out the specific constraint violation (e.g., "AS number 99999 exceeds max 4294967295")
- **Ambiguous** — Ask for clarification (e.g., "Should port1 and port2 be a static or LACP LAG?")

## Output Format

```json
{
  "ports": [...],
  "lags": [...],
  "devices": [...],
  "flows": [...],
  "lldp": [...],
  "captures": [...],
  "options": {...}
}
```

Omit empty arrays. Always include `ports`, `devices`, and `flows` at minimum.

## Example: Simple BGP Test

**User Input:**
```
Create a BGP test with 2 ports. Port1 runs BGP AS 65001 with 10.0.0.1/24,
peer with 10.0.0.2 AS 65002. Port2 runs BGP AS 65002 with 10.0.0.2/24,
peer with 10.0.0.1 AS 65001. Traffic from port1 to port2 at 1000 pps.
```

**Generated Config (JSON only):**
```json
{
  "ports": [
    {"name": "port1", "location": "port1"},
    {"name": "port2", "location": "port2"}
  ],
  "devices": [
    {
      "name": "device1",
      "ethernets": [
        {
          "name": "eth1",
          "connection": {"choice": "port_name", "port_name": "port1"},
          "mac": "00:11:22:33:44:55",
          "ipv4_addresses": [
            {
              "name": "ipv4_1",
              "address": "10.0.0.1",
              "prefix": 24,
              "gateway": "10.0.0.2"
            }
          ]
        }
      ],
      "bgp": {
        "router_id": "10.0.0.1",
        "ipv4_interfaces": [
          {
            "ipv4_name": "ipv4_1",
            "peers": [
              {
                "name": "bgp_peer_1",
                "peer_address": "10.0.0.2",
                "as_type": "ebgp",
                "as_number": 65002
              }
            ]
          }
        ]
      }
    },
    {
      "name": "device2",
      "ethernets": [
        {
          "name": "eth2",
          "connection": {"choice": "port_name", "port_name": "port2"},
          "mac": "00:11:22:33:44:66",
          "ipv4_addresses": [
            {
              "name": "ipv4_2",
              "address": "10.0.0.2",
              "prefix": 24,
              "gateway": "10.0.0.1"
            }
          ]
        }
      ],
      "bgp": {
        "router_id": "10.0.0.2",
        "ipv4_interfaces": [
          {
            "ipv4_name": "ipv4_2",
            "peers": [
              {
                "name": "bgp_peer_2",
                "peer_address": "10.0.0.1",
                "as_type": "ebgp",
                "as_number": 65001
              }
            ]
          }
        ]
      }
    }
  ],
  "flows": [
    {
      "name": "flow1",
      "tx_rx": {
        "choice": "port",
        "port": {
          "tx_name": "port1",
          "rx_names": ["port2"]
        }
      },
      "packet": [
        {"choice": "ethernet", "ethernet": {}},
        {"choice": "ipv4", "ipv4": {}}
      ],
      "rate": {"choice": "pps", "pps": 1000},
      "duration": {"choice": "continuous"}
    }
  ]
}
```

## Edge Cases

- **Device connection to LAG instead of port** — Use `connection.choice: "lag_name"` and reference the LAG
- **Multiple Ethernet interfaces per device** — Add multiple objects to `ethernets` array
- **VLAN-tagged traffic** — Include VLAN headers in flow packets or device Ethernet config
- **Stateful flows** — Use `stateful_flows` at top level (more complex, ask for clarification if needed)
- **Capture requirements** — Add to `captures` array with port and filter specs
- **Loopback addresses** — Use `ipv4_loopbacks` / `ipv6_loopbacks` on Device (NOT inside ethernets)
- **Device-based flows** — When traffic follows BGP learned routes, use `tx_rx.choice: "device"` with route range names as tx/rx
