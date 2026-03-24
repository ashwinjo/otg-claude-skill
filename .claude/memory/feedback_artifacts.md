---
name: Artifacts preservation strategy
description: Which generated files to preserve as reusable artifacts
type: feedback
---

## setup-ixia-c*.sh Scripts as Artifacts

**Rule:** Preserve `setup-ixia-c*.sh` scripts in `artifacts/deployment/` like OTG configs and Snappi scripts.

**Why:** These scripts are used frequently and represent validated deployment setup logic. Users should be able to reuse them without regenerating.

**How to apply:**
- When deployment agents generate `setup-ixia-c-*.sh`, save to `artifacts/deployment/`
- Add entry to `artifacts/deployment/INDEX.md` with columns: `File | Type | Ports | Method | Date | Notes`
- Cleanup command preserves these files (do NOT delete)
- Offer users choice: reuse existing script or generate new one

**Cleanup behavior:**
- PRESERVE: `artifacts/deployment/setup-ixia-c-*.sh` (validated scripts)
- PRESERVE: `docker-compose*.yml`, `*.clab.yml` in artifacts/ (validated configs)
- DELETE: Generated setup scripts in root directory (after copying to artifacts/)
- DELETE: docker-compose/topo files in root directory (after copying to artifacts/)

**Pattern:** Only root-level generated files are cleaned; artifacts/ folder persists across all cleanups.
