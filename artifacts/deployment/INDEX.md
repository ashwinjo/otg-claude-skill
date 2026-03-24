# Deployment Artifacts

Verified, working deployment configurations saved here for reuse.
Agents: check this index before generating new configs — list to user, ask reuse or regenerate.

| File | Protocol | Ports | Method | Date | Notes |
|------|----------|-------|--------|------|-------|
| b2b-dataplane-docker-compose.yml | Dataplane only | 2 (veth-a, veth-z) | Docker Compose, host network | 2026-03-24 | DP-only B2B, latest tags, location_map: veth-a→5555, veth-z→5556 |
