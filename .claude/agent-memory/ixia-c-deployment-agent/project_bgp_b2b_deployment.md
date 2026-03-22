---
name: BGP B2B Docker Compose deployment pattern
description: Confirmed deployment pattern for BGP back-to-back tests using CP+DP Docker Compose with veth pairs
type: project
---

BGP b2b testing requires the CP+DP (cpdp) topology — not the simpler dp-only topology — because protocol engines are needed for BGP/ISIS.

Files generated at: /home/ubuntu/otg-claude-skill/deployments/bgp-b2b/
- docker-compose.yml  — 5-service CP+DP stack
- setup-veth.sh       — veth creation, namespace push, location_map injection

**Why:** dp-only topology uses --net=host and veth on the host; cpdp uses bridge networking with veth pushed into container namespaces after startup. BGP needs protocol-engine co-located in the TE's netns.

**How to apply:** Whenever user asks for BGP or ISIS testing with Docker Compose, generate the 5-service CP+DP stack (controller + 2x TE + 2x PE) and the setup-veth.sh script. Do not use dp-only for protocol testing.

Port mapping output (template — IPs filled at runtime by setup-veth.sh):
- te1: location = veth-a  -> <TE_A_IP>:5555+<TE_A_IP>:50071
- te2: location = veth-z  -> <TE_Z_IP>:5555+<TE_Z_IP>:50071

OTG port location values for downstream agents: "veth-a" and "veth-z"
Controller URL: https://localhost:8443
