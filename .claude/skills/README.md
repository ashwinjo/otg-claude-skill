# OTG Config Generator Skill

**Status**: Ready for production use

## What This Skill Does

Converts natural language test scenario descriptions into valid Open Traffic Generator (OTG) JSON configurations. Your Agent can use this skill to:

- Generate configurations from user intent (e.g., "Create a BGP test with 2 ports")
- Understand the OTG OpenAPI schema and map scenarios to Config objects
- Validate all required fields, name uniqueness, and reference integrity
- Output production-ready JSON ready to push to an OTG device

## Key Capabilities

✅ Test Ports (L1/L2 configuration)
✅ Emulated Devices (L2/L3: IPv4, IPv6, ARP, ND)
✅ Routing Protocols (BGP, IS-IS)
✅ Port Aggregation (LACP, Static LAG)
✅ LLDP Configuration
✅ Traffic Flows (L2-4, stateless/stateful)
✅ VLAN Tagging
✅ Metrics & Capture Configuration
✅ Multi-device topologies with simulated links

## Tested Scenarios

1. ✅ Simple port-to-port traffic
2. ✅ BGP device-to-device peering
3. ✅ LAG with LACP configuration (verified pattern)
4. ✅ IS-IS multi-device topology (verified pattern)
5. ✅ Multi-flow VLAN tagging (verified pattern)

## How to Use

When your Agent needs to generate an OTG configuration:

```
User: "Create a BGP test with 2 ports and emulated devices..."
Agent: Uses otg-config-generator skill
Output: Valid OTG Config JSON ready to deploy
```

The skill returns ONLY JSON—no commentary. Your Agent can directly POST this to the OTG API.

## Files

- `SKILL.md` — Skill definition with workflow, patterns, and examples
- `evals/evals.json` — 5 test cases covering major use cases
- `README.md` — This file

## OpenAPI Spec Reference

Skill validated against: `/Users/ashwin.joshi/kengotg/openapi.yaml` (v1.49.0)

## Next Steps

1. Integrate this skill into your Agent
2. Agent calls skill with user scenarios
3. Skill returns JSON configuration
4. Agent pushes config to OTG API (e.g., `/config` POST endpoint)
