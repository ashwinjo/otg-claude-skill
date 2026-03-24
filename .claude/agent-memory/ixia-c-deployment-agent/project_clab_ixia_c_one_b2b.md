---
name: Containerlab ixia-c-one B2B loopback deployment
description: Validated deployment pattern for ixia-c-one B2B loopback using Containerlab (eth1 <-> eth2 on single node)
type: project
---

Containerlab ixia-c-one B2B loopback (topo name: ixcb2b) was successfully deployed.

**Why:** User needed a simple traffic-only B2B test without an external DUT, using ixia-c-one (all-in-one: controller + TE + PE) via Containerlab.

**How to apply:** Use `keysight_ixia-c-one` kind in topo.clab.yml with a single loopback link `endpoints: ["ixia-c:eth1", "ixia-c:eth2"]`. No location_map injection needed — controller auto-discovers ports via Containerlab links.

## Key facts

- Topo file: `/home/ubuntu/otg-claude-skill/topo.clab.yml`
- Setup script: `/home/ubuntu/otg-claude-skill/setup-clab-b2b.sh`
- Image: `ghcr.io/open-traffic-generator/ixia-c-one:1.48.0-5`
- Container name: `clab-ixcb2b-ixia-c`
- Container IP: `172.20.20.2` (assigned by Containerlab; auto-discover with `docker inspect`)
- Controller URL: `https://172.20.20.2:8443`
- Controller health check: `curl -sk https://172.20.20.2:8443/config` returns `{...options...}`

## Port mapping

| OTG port | Containerlab interface | Location value |
|----------|----------------------|----------------|
| P1       | eth1                 | eth1           |
| P2       | eth2                 | eth2           |

## Teardown

```bash
sudo containerlab destroy -t /home/ubuntu/otg-claude-skill/topo.clab.yml --cleanup
```
