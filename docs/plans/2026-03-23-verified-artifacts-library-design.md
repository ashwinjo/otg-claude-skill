# Verified Artifacts Library — Design

**Date:** 2026-03-23
**Status:** Approved
**Scope:** `artifacts/` folder system, INDEX.md catalog, SKILL.md pointers, cleanup command

---

## Problem

Every time a skill generates a deployment config or Snappi script, it starts from scratch. Once a config is verified and running, there is no mechanism to reuse it — the agent re-derives it, wasting time and risking drift from the known-good version.

---

## Solution

A lightweight artifact library at `artifacts/` that:
1. Stores verified, working deployment configs and Snappi scripts
2. Lets agents discover existing artifacts and present them to the user before generating new ones
3. Is maintained by agents themselves (auto-name, collision-aware)
4. Is never touched by `/kengotg-cleanup` — it is a permanent reference library

---

## Folder Structure

```
kengotg/
└── artifacts/
    ├── deployment/
    │   ├── INDEX.md                          <- catalog of verified deployment configs
    │   ├── bgp-2port-docker-compose.yml
    │   ├── bgp-4port-clab.yml
    │   └── ...
    └── snappi-scripts/
        ├── INDEX.md                          <- catalog of verified Snappi scripts
        ├── bgp-2port-test.py
        ├── bgp-4port-test.py
        └── ...
```

- `artifacts/` lives at repo root alongside `README.md` and `AGENT_ORCHESTRATION_PLAN.md`
- The two subfolders are independent — each skill manages its own INDEX.md
- No other folders are created

---

## INDEX.md Format

### `artifacts/deployment/INDEX.md`

```markdown
# Deployment Artifacts

| File | Protocol | Ports | Method | Date | Notes |
|------|----------|-------|--------|------|-------|
| bgp-2port-docker-compose.yml | BGP | 2 | Docker Compose (cpdp) | 2026-03-23 | Verified — b2b, AS 65001/65002 |
| bgp-4port-clab.yml | BGP | 4 | Containerlab (ixia-c-one) | 2026-03-23 | Verified — spine-leaf lab |
```

### `artifacts/snappi-scripts/INDEX.md`

```markdown
# Snappi Script Artifacts

| File | Protocol | Ports | Controller | Date | Notes |
|------|----------|-------|------------|------|-------|
| bgp-2port-test.py | BGP | 2 | localhost:8443 | 2026-03-23 | Verified — b2b convergence test |
| bgp-4port-test.py | BGP | 4 | 10.0.0.1:8443 | 2026-03-23 | Verified — spine-leaf traffic test |
```

---

## SKILL.md Pointer Pattern

### `ixia-c-deployment/SKILL.md` — new step at top

```
> 📁 Before generating any deployment config, check `artifacts/deployment/INDEX.md`
> for existing verified configs. List them to the user and ask: reuse or regenerate?
> If saving a new config, append a row to INDEX.md. On name collision, ask: overwrite or keep both?
```

### `snappi-script-generator/SKILL.md` — new step at top

```
> 📁 Before generating any Snappi script, check `artifacts/snappi-scripts/INDEX.md`
> for existing verified scripts. List them to the user and ask: reuse or regenerate?
> If saving a new script, append a row to INDEX.md. On name collision, ask: overwrite or keep both?
```

Both pointers follow the same style as the existing `fixes.md` pointer already in each SKILL.md.

---

## Agent Behavior Flow

```
Agent invoked (deployment or script generation)
  └─> Read artifacts/<folder>/INDEX.md
        ├─ File exists + has entries?
        │     └─> List entries to user
        │           └─> User picks: REUSE → return existing file path
        │                          REGENERATE → proceed with generation
        └─ File empty or does not exist?
              └─> Proceed with generation directly

After generation (new file):
  └─> Derive descriptive filename from scenario (e.g. bgp-2port-docker-compose.yml)
        ├─ Name not in INDEX.md → save file, append row to INDEX.md
        └─ Name already in INDEX.md → ask: overwrite or keep both?
              ├─ Overwrite → replace file, update INDEX.md row
              └─ Keep both → append suffix (-v2, -v3, etc.), save, append new row
```

---

## `/kengotg-cleanup` Change

**No functional change to cleanup behavior.** The command continues to tear down:
- Ixia-c Docker containers
- Containerlab topologies
- veth pairs
- netns symlinks

**What we add:** A single clarifying note in the command's "What This Command Does" section:

> This command does not modify `artifacts/` — your verified deployment configs and Snappi scripts are preserved.

The `artifacts/` folder is a permanent library and is never emptied by any automated command.

---

## Files to Create / Modify

| Action | File |
|--------|------|
| Create | `artifacts/deployment/INDEX.md` (empty table, ready to populate) |
| Create | `artifacts/snappi-scripts/INDEX.md` (empty table, ready to populate) |
| Modify | `.claude/skills/ixia-c-deployment/SKILL.md` — add artifacts pointer |
| Modify | `.claude/skills/snappi-script-generator/SKILL.md` — add artifacts pointer |
| Modify | `.claude/commands/kengotg-cleanup.md` — add clarifying note |

---

## Non-Goals

- No automated validation of artifacts (agent trusts "verified" label from user)
- No version history within artifacts (git handles that)
- No cross-folder catalog (each skill manages its own INDEX.md independently)
- Cleanup command does not touch artifacts under any circumstance
