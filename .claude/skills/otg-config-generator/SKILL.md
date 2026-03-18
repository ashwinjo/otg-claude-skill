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

**Emulated Device** — Typical structure:
```json
{
  "name": "device1",
  "container_name": "device1",
  "device_eth": [
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
  "bgp": [
    {
      "name": "bgp",
      "router_id": "10.0.0.1",
      "asn": 65001,
      "ipv4_unicast": {
        "sendunicast": true
      },
      "neighbors": [...]
    }
  ]
}
```

**Traffic Flow** — Typical structure:
```json
{
  "name": "flow1",
  "tx_port": "port1",
  "rx_ports": ["port2"],
  "packet": [
    {
      "name": "eth",
      "header": {
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

**BGP Neighbor** — For protocol testing:
```json
{
  "peer_address": "10.0.0.254",
  "as_number": 65002,
  "name": "bgp_neighbor_1"
}
```

**BGP Route Advertisement** — Advertising prefixes to a peer:
```json
{
  "name": "bgp_neighbor_1",
  "peer_address": "10.0.0.254",
  "as_number": 65002,
  "v4_routes": [
    {
      "name": "routes_v4",
      "addresses": [
        {"address": "10.0.0.0", "prefix": 24, "count": 100, "step": 1}
      ]
    }
  ]
}
```
`count` = number of prefixes, `step` = increment between prefixes (1 = 10.0.0.0/24, 10.0.1.0/24, ..., 10.0.99.0/24).

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

**LACP LAG** — For port aggregation:
```json
{
  "name": "lag1",
  "ports": [
    {
      "port_name": "port1",
      "ethernet": { ... },
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

1. **All required fields present** — Every object has its required fields
2. **Name uniqueness** — Global uniqueness for all named objects (ports, devices, flows, etc.)
3. **Reference integrity** — Device Ethernet connections reference existing ports or LAGs
4. **Flow connectivity** — tx_port and rx_ports exist and are valid
5. **Constraint compliance** — LAG ports (1-32), prefix lengths (valid ranges), AS numbers, etc.
6. **Protocol consistency** — BGP with IPv4/IPv6 unicast, correct neighbor AS numbers, etc.

### Step 4: Return Configuration

Output a complete `Config` object with these top-level arrays:

```json
{
  "ports": [...],
  "lags": [...],
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
1 Tx port → 1 Rx port → 1 Flow

### Device-to-Device BGP Test
- Device 1: Port1, IPv4 10.0.0.1/24, BGP AS 65001
- Device 2: Port2, IPv4 10.0.0.2/24, BGP AS 65002
- Flow: From Device1 eth to Device2 eth

### LAG with LACP
- Port1 + Port2 → LAG1
- Device connected to LAG1
- Device starts LACP on LAG1

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
    { "name": "port1", "location": "port1" },
    { "name": "port2", "location": "port2" }
  ],
  "devices": [
    {
      "name": "device1",
      "container_name": "device1",
      "device_eth": [
        {
          "name": "eth1",
          "connection": {"choice": "port_name", "port_name": "port1"},
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
      "bgp": [
        {
          "name": "bgp",
          "router_id": "10.0.0.1",
          "asn": 65001,
          "ipv4_unicast": {"sendunicast": true},
          "neighbors": [
            {
              "name": "bgp_neighbor_1",
              "peer_address": "10.0.0.2",
              "as_number": 65002
            }
          ]
        }
      ]
    },
    {
      "name": "device2",
      "container_name": "device2",
      "device_eth": [
        {
          "name": "eth1",
          "connection": {"choice": "port_name", "port_name": "port2"},
          "mac": "00:11:22:33:44:66",
          "ipv4_addresses": [
            {
              "name": "ipv4_1",
              "address": "10.0.0.2",
              "prefix": 24,
              "gateway": "10.0.0.254"
            }
          ]
        }
      ],
      "bgp": [
        {
          "name": "bgp",
          "router_id": "10.0.0.2",
          "asn": 65002,
          "ipv4_unicast": {"sendunicast": true},
          "neighbors": [
            {
              "name": "bgp_neighbor_1",
              "peer_address": "10.0.0.1",
              "as_number": 65001
            }
          ]
        }
      ]
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
        {
          "name": "eth",
          "header": {
            "choice": "ethernet",
            "ethernet": {}
          }
        },
        {
          "name": "ipv4",
          "header": {
            "choice": "ipv4",
            "ipv4": {}
          }
        }
      ],
      "rate": {"choice": "pps", "pps": 1000},
      "duration": {"choice": "continuous"}
    }
  ]
}
```

## Edge Cases

- **Device connection to LAG instead of port** — Use `connection.choice: "lag_name"` and reference the LAG
- **Multiple Ethernet interfaces per device** — Add multiple objects to `device_eth` array
- **VLAN-tagged traffic** — Include VLAN headers in flow packets or device Ethernet config
- **Stateful flows** — Use `stateful_flows` at top level (more complex, ask for clarification if needed)
- **Capture requirements** — Add to `captures` array with port and filter specs
