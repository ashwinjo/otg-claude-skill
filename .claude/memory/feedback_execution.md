---
name: Execution patterns
description: Core behavioral rules for skill execution and code edits
type: feedback
---

## Mandatory: Read fixes.md Before Skill Execution

**Rule:** Before generating output for ANY skill, read the skill's `fixes.md` in `.claude/skills/<skill-name>/fixes.md`

**Why:** Repeated failures due to skipped fixes.md review; known patterns weren't being consulted

**How to apply:**
1. Classify the task (which skill?)
2. Immediately read that skill's fixes.md
3. Catalog all known wrong/right patterns
4. Cross-check generated output against those patterns
5. When encountering new failures, add to fixes.md

**Skills with fixes.md:**
- `.claude/skills/otg-config-generator/fixes.md`
- `.claude/skills/snappi-script-generator/fixes.md`
- `.claude/skills/ixia-c-deployment/fixes.md`
- `.claude/skills/keng-licensing/fixes.md`
- `.claude/skills/ixnetwork-to-keng-converter/fixes.md`

---

## Surgical Edits, Not Rewrites

**Rule:** When asked to change a test parameter in an existing script, use Edit tool to modify only the affected lines. Do NOT rewrite the entire script.

**Why:** Preserve existing code structure, avoid unnecessary churn, maintain user's original work

**How to apply:**
- User says: "change param C to M in the script"
- Read the script first with Read tool
- Use Edit tool to target only the line(s) where C appears
- Never use Write tool for this (that rewrites everything)

**Example pattern:**
```
Read script → identify 2-3 lines with param C → Edit each line → done
NOT: Read script → Write completely new script
```

---

## Ask Before Executing Generated Scripts

**Rule:** After generating or modifying a test script, ASK the user if they want Claude to run it or if they prefer to run it themselves. Do NOT automatically execute.

**Why:** Respect user autonomy. User may want to review the script first, run it in a specific environment, or test it themselves.

**How to apply:**
- Generate/modify script
- Show the user what was created
- Ask: "Would you like me to run this with `python3 test_xxx.py --auto-start`, or would you prefer to run it yourself?"
- Wait for user response before executing

**Never do:** Generate script → immediately run it without asking

---

## Port Location Alignment is Critical

**Rule:** Always validate port location alignment between deployment infrastructure and OTG configuration before proceeding to script generation.

**Why:** Scripts fail at runtime with connection errors if port mappings don't align

**How to apply:**
1. After deployment: Verify port_mapping has all required locations
2. Before config generation: Cross-check port count matches deployment
3. Before script generation: Ensure OTG config port locations match infrastructure ports
4. If ANY misalignment: Stop and clarify with user before proceeding

**Example mismatch:** Deployment returns `te1:location_1:5555, te2:location_2:5556` but OTG config uses `port-1:veth-a, port-2:veth-b` → FAIL

---

## Standalone Script Generation

**Rule:** All generated Snappi scripts must be self-contained with zero external dependencies (except snappi SDK).

**Why:** Users should be able to copy script and run immediately: `python test_xxx.py`

**How to apply:**
- Embed ALL infrastructure details (controller URL, ports, credentials) in script
- No external config files required
- No relative paths to configs
- All OTG config JSON embedded as string literals
- Users only need: `pip install snappi && python test_xxx.py`

---

## Memory Location

**Rule:** All project memory is stored in `.claude/memory/` folder (checked into git) and/or skill-specific `fixes.md` files.

**Why:** Portable across servers, version-controlled, reusable

**How to apply:**
- Project-level learnings → `.claude/memory/*.md`
- Skill-specific patterns → `.claude/skills/<skill>/fixes.md`
- Index files → `MEMORY.md` + `artifacts/*/INDEX.md`
- Never rely on user-home auto-memory (not transportable)
