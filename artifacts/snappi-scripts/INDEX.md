# Snappi Script Artifacts

Verified, working Snappi test scripts saved here for reuse.
Agents: check this index before generating new scripts — list to user, ask reuse or regenerate.

| File | Protocol | Ports | Controller | Date | Notes |
|------|----------|-------|------------|------|-------|
| test_b2b_dataplane.py | none (L2/L3 dataplane) | 2 (localhost:5555, localhost:5556) | https://localhost:8443 | 2026-03-24 | 64-byte frames, 100% line rate, bidirectional, 30s, 1s metrics interval, generated for Docker Compose deployment |
| test_b2b_dataplane_1500bytes.py | none (L2/L3 dataplane) | 2 (localhost:5555, localhost:5556) | https://localhost:8443 | 2026-03-23 | 1500-byte jumbo frames, 100% line rate, 10G, bidirectional, 60s, 1s metrics interval |
| test_b2b_dataplane_128byte.py | none (L2/L3 dataplane) | 2 (veth-a, veth-z) | https://localhost:8443 | 2026-03-24 | 128-byte frames, 1000 pps, bidirectional, 30s, 1s metrics interval, Ethernet+IPv4 headers |
