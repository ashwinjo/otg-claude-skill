# fixes.md — ixia-c-deployment

Known failure patterns for this skill. Read this before generating any output.
New entries go at the bottom. Duplicate cross-cutting fixes here — skills are self-contained.

---

### [Deployment] CRITICAL: Never Use ixia-c-one for Docker Compose
**Wrong:** Using `ghcr.io/open-traffic-generator/ixia-c-one` in a Docker Compose file for standalone deployments
**Right:** Docker Compose must use separate containers: `keng-controller` + `ixia-c-traffic-engine` (+ `ixia-c-protocol-engine` if protocols needed)
**Why:** ixia-c-one is optimized for Containerlab multi-node topologies only — it has architectural constraints that limit throughput to ~1.8 Gbps and disables flow-level metrics

```yaml
# WRONG — Docker Compose with ixia-c-one
services:
  ixia-c:
    image: ghcr.io/open-traffic-generator/ixia-c-one:latest

# RIGHT — Docker Compose with separate containers
services:
  keng-controller:
    image: ghcr.io/open-traffic-generator/keng-controller:latest
  ixia-c-te1:
    image: ghcr.io/open-traffic-generator/ixia-c-traffic-engine:latest
```

Decision table:
- Docker Compose B2B → keng-controller + ixia-c-traffic-engine (never ixia-c-one)
- Docker Compose CP+DP → keng-controller + ixia-c-traffic-engine + ixia-c-protocol-engine
- Containerlab single-node → ixia-c-one (correct use case)
- Containerlab multi-node → ixia-c-one per node (correct use case)

---

### [Deployment] Controller REST Endpoint is /config, Not /api/v1/config
**Wrong:** `curl -k https://localhost:8443/api/v1/config`
**Right:** `curl -k https://localhost:8443/config`
**Why:** Ixia-c controller does not use the `/api/v1/` prefix; the pattern is common in other systems but not here — returns HTTP 404

---

### [API/TLS] Always Use curl -k for Ixia-c Controller
**Wrong:** `curl https://localhost:8443/config`
**Right:** `curl -k https://localhost:8443/config`
**Why:** Ixia-c controller uses self-signed HTTPS certificates by default; standard curl rejects them, producing repeated TLS handshake errors in controller logs

---

### [Deployment] Host Network Mode: Port Discovery via Logs, Not docker inspect
**Wrong:** Using `docker inspect <container>` to find exposed ports for host-network containers
**Right:** Parse controller startup logs: `docker logs keng-controller | grep "HTTPS Server started"`
**Why:** `docker inspect` shows empty `"Ports": {}` for `network_mode: host` containers — ports are not port-mapped, they're directly on the host network

```bash
# WRONG — returns empty Ports for host-network containers
docker inspect keng-controller | jq '.[0].NetworkSettings.Ports'

# RIGHT
docker logs keng-controller | grep "HTTPS Server started\|HTTPPort"
# Output: {"msg":"HTTPS Server started","addr":":8443"...}
# Default ports: HTTPS 8443, GRPC 40051
```

---

### [Deployment] docker cp config.yaml: Always chmod 644 After Copy
**Wrong:** `docker cp config.yaml keng-controller:/home/ixia-c/controller/config/` without follow-up chmod
**Right:** Add `sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml` immediately after
**Why:** `docker cp` sets mode 600 owned by root; the controller process runs as non-root and returns HTTP 500 `permission denied`

```bash
# RIGHT
docker cp config.yaml keng-controller:/home/ixia-c/controller/config/config.yaml
sudo docker exec -u root keng-controller chmod 644 /home/ixia-c/controller/config/config.yaml
```

---

### [Deployment] Containerlab: Controller IP Is Not localhost
**Wrong:** Using `https://localhost:8443` for a Containerlab-deployed ixia-c-one
**Right:** Discover the container IP after deploy
**Why:** ixia-c-one runs on Containerlab's internal Docker bridge, not the host — `localhost` resolves to the host machine (Connection refused)

```bash
# Discover IP after containerlab deploy
IXIA_IP=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' clab-<topo-name>-ixia-c)
# Use: https://${IXIA_IP}:8443
```

---

### [Deployment] Containerlab Multi-Node Pattern (Validated)
**Wrong:** N/A — this is a success pattern
**Right:** Each ixia-c-one node is independently accessible at its container IP:8443; push separate OTG configs per node; FRR BGP neighbors point to ixia eth1 IPs
**Why:** Documenting the validated topology: multiple ixia-c-one nodes + FRR DUT in Containerlab, with independent per-node API access
