# Verified Artifacts Library Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create an `artifacts/` library where verified deployment configs and Snappi scripts are stored, cataloged via INDEX.md, and discoverable by agents before generating new output.

**Architecture:** Two independent subfolders (`artifacts/deployment/` and `artifacts/snappi-scripts/`), each with an INDEX.md catalog table maintained by agents. SKILL.md files get pointer steps directing agents to check the catalog first. The cleanup command gets a note explicitly preserving the library.

**Tech Stack:** Markdown files only — no code changes required.

**Design doc:** `docs/plans/2026-03-23-verified-artifacts-library-design.md`

---

### Task 1: Create `artifacts/deployment/INDEX.md`

**Files:**
- Create: `artifacts/deployment/INDEX.md`

**Step 1: Create the file**

```markdown
# Deployment Artifacts

Verified, working deployment configurations saved here for reuse.
Agents: check this index before generating new configs — list to user, ask reuse or regenerate.

| File | Protocol | Ports | Method | Date | Notes |
|------|----------|-------|--------|------|-------|
```

**Step 2: Verify the file was created**

```bash
cat artifacts/deployment/INDEX.md
```

Expected: the table header with no data rows yet.

**Step 3: Commit**

```bash
git add artifacts/deployment/INDEX.md
git commit -m "feat: add artifacts/deployment with empty INDEX.md catalog"
```

---

### Task 2: Create `artifacts/snappi-scripts/INDEX.md`

**Files:**
- Create: `artifacts/snappi-scripts/INDEX.md`

**Step 1: Create the file**

```markdown
# Snappi Script Artifacts

Verified, working Snappi test scripts saved here for reuse.
Agents: check this index before generating new scripts — list to user, ask reuse or regenerate.

| File | Protocol | Ports | Controller | Date | Notes |
|------|----------|-------|------------|------|-------|
```

**Step 2: Verify the file was created**

```bash
cat artifacts/snappi-scripts/INDEX.md
```

Expected: the table header with no data rows yet.

**Step 3: Commit**

```bash
git add artifacts/snappi-scripts/INDEX.md
git commit -m "feat: add artifacts/snappi-scripts with empty INDEX.md catalog"
```

---

### Task 3: Add artifacts pointer to `ixia-c-deployment/SKILL.md`

**Files:**
- Modify: `.claude/skills/ixia-c-deployment/SKILL.md:12-13`

**Context:** Line 12 currently reads:
```
> ⚠️ Read `fixes.md` in this directory before generating any output.
```

**Step 1: Insert the artifacts pointer on line 13 (blank line after fixes.md pointer)**

Add the following block immediately after line 12:

```markdown
> 📁 Before generating any deployment config, read `artifacts/deployment/INDEX.md`.
> List existing verified configs to the user and ask: **reuse** or **regenerate**?
> When saving a new config: derive a descriptive filename (e.g. `bgp-2port-docker-compose.yml`),
> append a row to `artifacts/deployment/INDEX.md`. On name collision: ask overwrite or keep both.
```

After the edit, lines 12–17 should look like:

```
> ⚠️ Read `fixes.md` in this directory before generating any output.

> 📁 Before generating any deployment config, read `artifacts/deployment/INDEX.md`.
> List existing verified configs to the user and ask: **reuse** or **regenerate**?
> When saving a new config: derive a descriptive filename (e.g. `bgp-2port-docker-compose.yml`),
> append a row to `artifacts/deployment/INDEX.md`. On name collision: ask overwrite or keep both.

## Step 0: Check if deployment already exists
```

**Step 2: Verify the edit**

```bash
head -20 .claude/skills/ixia-c-deployment/SKILL.md
```

Expected: both the `fixes.md` warning and the new `artifacts` pointer visible.

**Step 3: Commit**

```bash
git add .claude/skills/ixia-c-deployment/SKILL.md
git commit -m "feat: add artifacts library pointer to ixia-c-deployment SKILL.md"
```

---

### Task 4: Add artifacts pointer to `snappi-script-generator/SKILL.md`

**Files:**
- Modify: `.claude/skills/snappi-script-generator/SKILL.md:19-20`

**Context:** Line 19 currently reads:
```
> ⚠️ Read `fixes.md` in this directory before generating any output.
```

**Step 1: Insert the artifacts pointer on line 20 (blank line after fixes.md pointer)**

Add the following block immediately after line 19:

```markdown
> 📁 Before generating any Snappi script, read `artifacts/snappi-scripts/INDEX.md`.
> List existing verified scripts to the user and ask: **reuse** or **regenerate**?
> When saving a new script: derive a descriptive filename (e.g. `bgp-2port-test.py`),
> append a row to `artifacts/snappi-scripts/INDEX.md`. On name collision: ask overwrite or keep both.
```

After the edit, lines 19–24 should look like:

```
> ⚠️ Read `fixes.md` in this directory before generating any output.

> 📁 Before generating any Snappi script, read `artifacts/snappi-scripts/INDEX.md`.
> List existing verified scripts to the user and ask: **reuse** or **regenerate**?
> When saving a new script: derive a descriptive filename (e.g. `bgp-2port-test.py`),
> append a row to `artifacts/snappi-scripts/INDEX.md`. On name collision: ask overwrite or keep both.

Generate executable Python Snappi scripts from OTG configurations and infrastructure specifications.
```

**Step 2: Verify the edit**

```bash
head -28 .claude/skills/snappi-script-generator/SKILL.md
```

Expected: both the `fixes.md` warning and the new `artifacts` pointer visible.

**Step 3: Commit**

```bash
git add .claude/skills/snappi-script-generator/SKILL.md
git commit -m "feat: add artifacts library pointer to snappi-script-generator SKILL.md"
```

---

### Task 5: Add clarifying note to `kengotg-cleanup.md`

**Files:**
- Modify: `.claude/commands/kengotg-cleanup.md:14-15`

**Context:** Line 14 currently reads:
```
Runs a multi-step cleanup sequence. Each step is independent — failures in one step don't block the others.
```

**Step 1: Insert a note after line 14**

Add the following block immediately after line 14 (before `### Step 1`):

```markdown
> **Note:** This command does not modify `artifacts/` — your verified deployment configs and Snappi scripts are preserved across cleanups.
```

After the edit, lines 12–18 should look like:

```
## What This Command Does

Runs a multi-step cleanup sequence. Each step is independent — failures in one step don't block the others.

> **Note:** This command does not modify `artifacts/` — your verified deployment configs and Snappi scripts are preserved across cleanups.

### Step 1: Stop and remove Ixia-c Docker containers
```

**Step 2: Verify the edit**

```bash
head -22 .claude/commands/kengotg-cleanup.md
```

Expected: clarifying note visible between the intro paragraph and Step 1.

**Step 3: Commit**

```bash
git add .claude/commands/kengotg-cleanup.md
git commit -m "docs: clarify artifacts/ is preserved by kengotg-cleanup"
```

---

## Completion Checklist

- [ ] `artifacts/deployment/INDEX.md` exists with empty table
- [ ] `artifacts/snappi-scripts/INDEX.md` exists with empty table
- [ ] `ixia-c-deployment/SKILL.md` has artifacts pointer after `fixes.md` line
- [ ] `snappi-script-generator/SKILL.md` has artifacts pointer after `fixes.md` line
- [ ] `kengotg-cleanup.md` has note that `artifacts/` is never touched
- [ ] 5 clean commits (one per task)
