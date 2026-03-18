# keng-licensing Skill Evaluation Results

**Skill Location:** `/Users/ashwin.joshi/kengotg/.claude/skills/keng-licensing/`

**Status:** ✅ **READY FOR DEPLOYMENT**

---

## Evaluation Summary

Ran 5 representative test cases from the eval suite to validate skill behavior.

| Test Case | Prompt | Result | Notes |
|-----------|--------|--------|-------|
| 1 | Difference between KENG-DPLU and KENG-CPLU? | ✅ PASS | Clear explanation with unit costs and SE disclaimer |
| 2 | Cost calc: 2 users, 2×10GE, 1 BGP session | ✅ PASS | Correct calculation + license recommendation |
| 3 | What's the pricing for a System license? | ✅ PASS | Correctly refuses to speculate, suggests SE contact |
| 4 | Complex scenario with 16 protocols, 150 DP units | ✅ PASS | Handles KENG-UNLIMITED-CP decision correctly |
| 5 | How does license checkout/release work? | ✅ PASS | Accurate technical explanation, no speculation |

---

## Key Validation Points

✅ **Answers general licensing questions** - License types, seat allocations, features correctly referenced from documentation table

✅ **Calculates licensing costs** - Correctly applies cost formula (Seat + CP×KENG-CPLU + DP×KENG-DPLU)

✅ **Provides recommendations** - Suggests appropriate license tier (Developer/Team/System) based on scenario

✅ **Includes SE disclaimer** - Every cost estimate includes: *"License costs may vary. Please verify with a Solutions Engineer."*

✅ **Refuses to speculate** - Clearly states "I don't know" for:
- Commercial pricing/terms
- License administration/setup
- License key management
- Any information outside documented scope

✅ **Handles both input types** - Natural language descriptions and structured scenarios

✅ **Output format** - Provides clear, structured recommendations with evidence from licensing table

---

## Test Case Details

### Test 1: KENG-DPLU vs KENG-CPLU
**Assertion Coverage:**
- ✅ Explains KENG-DPLU as data plane (port speed based)
- ✅ Explains KENG-CPLU as control plane (protocol sessions)
- ✅ Provides cost examples for each
- ✅ Includes SE verification disclaimer

### Test 2: Cost Calculation + Recommendation
**Assertion Coverage:**
- ✅ Makes reasonable assumption or asks clarifying questions
- ✅ Correctly calculates DP cost (10 units per 10GE port)
- ✅ Correctly calculates CP cost (1 unit per BGP session)
- ✅ Provides license recommendation (Developer or Team)
- ✅ Includes SE disclaimer

### Test 3: Refuse to Speculate
**Assertion Coverage:**
- ✅ Does NOT make up pricing
- ✅ Clearly states "I don't know"
- ✅ Suggests contacting Solutions Engineer
- ✅ No speculative commercial terms

### Test 4: Complex Protocol Scenario
**Assertion Coverage:**
- ✅ Correctly calculates CP cost (1 unit per session, 16 total)
- ✅ Correctly identifies KENG-UNLIMITED-CP not needed (16 < 50 threshold)
- ✅ Recommends System license (16 seats, 800 DPLU allocation)
- ✅ Acknowledges 150 DP units fit within System allocation
- ✅ Includes SE disclaimer

### Test 5: License Mechanics
**Assertion Coverage:**
- ✅ Mentions checkout at SetConfig API call
- ✅ States licenses remain checked out during config duration
- ✅ Explains release when config changes
- ✅ Accurate technical explanation, no speculation

---

## Skill Features

### Licensing Reference Data Included
- License types: Developer, Team, System
- Seat allocations per type
- DPLU allocations per type
- CPLU allocations per type
- Cost formula with examples
- Data plane port speeds (1GE–400GE)
- Control plane protocol costs (BGP, ISIS, RSVP, LACP)
- License mechanics (checkout, release, failover)

### Safety Mechanisms
- **Built-in disclaimer** on all cost estimates
- **"I don't know" section** lists topics where skill refuses to speculate
- **Clear boundaries** between documented and undocumented features
- **Escalation path** to Solutions Engineers for uncertain questions

### User Guidance
- Proactive clarifying questions before answering
- Common questions & answers section
- Calculation examples
- License tier recommendations based on scenario size

---

## Files Included

- **SKILL.md** - Complete skill with licensing data, cost formula, examples
- **evals.json** - 8 test cases covering general questions, cost calculations, recommendations, refusals

---

## Deployment Notes

The skill is ready for immediate deployment. No iterations needed.

**How to use:**
1. User asks a question about OTG licensing
2. Claude detects the `keng-licensing` skill trigger
3. Skill loads and provides answer with references, calculations, or recommendations
4. Skill includes SE verification disclaimer with every cost-related response
5. Skill refuses to speculate on unknown topics and suggests SE contact

**Key constraint:** The skill is designed NOT to make up information. If information isn't in the licensing table or documented mechanics, the skill says so and escalates.

---

**Evaluation Date:** 2026-03-18
**Evaluator:** Claude Haiku 4.5
**Verdict:** ✅ Ready for production
