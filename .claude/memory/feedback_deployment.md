---
name: Deployment preferences
description: User preferences for infrastructure deployment
type: feedback
---

## Skip Redeployment if Containers Exist

**Rule:** Before deploying, always check if containers are already running that match the requested scenario.

**Why:** User wants to avoid redundant deployments and reuse existing infrastructure when possible

**How to apply:**
1. First: Run `docker ps` to check for running ixia-c/keng containers
2. If containers exist: Ask user — "Infrastructure found. Reuse or redeploy?"
3. Only proceed with new deployment if user explicitly confirms
4. Default to reuse (less disruptive)

**Command to check:**
```bash
docker ps --filter "name=ixia-c\|keng-" --format "table {{.Names}}\t{{.Status}}"
```

---

## Use Latest Image Tags

**Rule:** When deploying, default to `latest` image tag instead of pinned versions unless explicitly requested.

**Why:** Keeps deployments current with latest patches and features

**How to apply:**
- Use: `ghcr.io/open-traffic-generator/keng-controller:latest`
- Not: `ghcr.io/open-traffic-generator/keng-controller:1.48.0-5`
- Exception: If user specifies a version, use exactly that
