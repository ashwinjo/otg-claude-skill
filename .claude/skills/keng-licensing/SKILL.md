---
name: keng-licensing
description: |
  Answers questions about OTG (Open Traffic Generator / KENG) licensing.
  Use this skill whenever the user asks about:
  - License types and seat allocations (Developer, Team, System)
  - Licensing features (KENG-SEAT, KENG-DPLU, KENG-CPLU, KENG-UNLIMITED-CP)
  - Cost calculations for data plane (port speeds) and control plane (protocols)
  - Which license to choose for a given scenario
  - How licensing works (checkout, release, failover)

  Provides cost estimates and recommendations, with clear disclaimers that costs may vary
  and users should verify with a Solutions Engineer. Never makes up pricing or feature information.
---

# OTG Licensing Reference Tool

> ⚠️ Read `fixes.md` in this directory before generating any output.

## Core Principle

**Do NOT make up information.** If you don't know the answer, say so clearly and suggest the user contact a Solutions Engineer (SE).

Always include a disclaimer: *"License costs may vary. Please verify with a Solutions Engineer for exact pricing and your specific use case."*

---

## License Types & Seat Allocations

| License Type | Developer | Team | System |
|---|---|---|---|
| KENG-SEAT | 1 | 8 | 16 |
| KENG-SEAT-UHD | N/A | 8 | 16 |
| KENG-SEAT-IXHW | N/A | N/A | 16 |
| KENG-DPLU | 50 | 400 | 800 |
| KENG-CPLU | 50 | 400 | 800 |
| KENG-UNLIMITED-CP | N/A | N/A | 16 |

**Abbreviations:**
- KENG-SEAT: License seats (concurrent user sessions)
- KENG-SEAT-UHD: Ultra high-density seats (Team/System only)
- KENG-SEAT-IXHW: IxHardware seats (System only)
- KENG-DPLU: Data Plane License Units (port speed based)
- KENG-CPLU: Control Plane License Units (protocol sessions)
- KENG-UNLIMITED-CP: Unlimited control plane (caps CP cost at 50 units)

---

## Cost Calculation

### Formula
```
Test Cost = Seat Cost + (CP Cost × KENG-CPLU) + (DP Cost × KENG-DPLU)
```

### Data Plane Costs (KENG-DPLU)
Port speed determines DP cost in license units:
- 1GE = 1 unit
- 10GE = 10 units
- 25GE = 25 units
- 40GE = 40 units
- 100GE = 100 units
- 200GE = 200 units
- 400GE = 400 units

### Control Plane Costs (KENG-CPLU)
Cost per protocol session:
- **BGP**: 1 unit per session
- **ISIS**: 1 unit per session
- **RSVP**: 1 unit per session
- **LACP**: 1 unit per session
- **IP Interfaces**: 0 units (no cost)

### Control Plane Optimization
- When CP Cost > 50 units, the KENG-UNLIMITED-CP license consolidates the cost to 50 units flat
- This avoids unbounded CP costs for heavy protocol configurations

---

## License Mechanics

### Checkout & Release
- Licenses check out at **OTG SetConfig API call**
- Licenses remain checked out for the **configuration duration**
- Licenses are **released when configurations change**

### Server Failover
- System supports up to **4 license servers**
- Automatic failover if a server becomes unavailable
- No manual intervention required

---

## Before Answering Questions

When a user asks about licensing, first ask clarifying questions to understand their scenario:

1. **Scope**: Are they asking about general licensing info or a specific test scenario?
2. **Test Configuration** (if applicable):
   - How many concurrent seats/users?
   - What port speeds? (1GE, 10GE, 100GE, etc.)
   - What protocols? (BGP, ISIS, RSVP, LACP, etc.)
   - How many protocol sessions per protocol?
3. **License Edition**: Do they prefer Developer, Team, or System?
4. **Cost Priority**: Are they optimizing for cost or capacity?

---

## Common Questions & Answers

### "What's the difference between KENG-DPLU and KENG-CPLU?"
- **KENG-DPLU** (Data Plane): Port speed cost. More ports or higher speeds = higher cost.
- **KENG-CPLU** (Control Plane): Protocol session cost. More protocol sessions = higher cost.
- Both are consumed per test configuration.

### "Can I mix licenses?"
- **Not explicitly documented.** Don't assume. Suggest contacting an SE.

### "What happens if I exceed my license limit?"
- **Not documented.** Don't guess. Suggest contacting an SE.

### "Do I need KENG-UNLIMITED-CP?"
- Only if your CP Cost will exceed 50 units. Calculate first; if CP cost ≤ 50, don't need it.

### "Which license should I choose?"
Recommend based on:
- **Developer**: Single user, small tests, R&D
- **Team**: 2-8 concurrent users, moderate-scale tests
- **System**: 16 concurrent users, large-scale production tests

---

## Calculation Example

**Scenario**: Team license, 4 concurrent seats, 2× 100GE ports, 1× BGP session, 1× ISIS session

```
Seat Cost = 8 seats available (Team tier)
DP Cost = (100 units × 2 ports) = 200 units
CP Cost = (1 BGP session) + (1 ISIS session) = 2 units

Test Cost = 8 + (2 × KENG-CPLU) + (200 × KENG-DPLU)
(Assuming base KENG-CPLU and KENG-DPLU allocations from Team tier: 400 each)
Total cost in units = 8 + 2 + 200 = 210 license units consumed
```

**Note**: This is illustrative. Actual cost structure depends on licensing model (consumption-based, seat-based, etc.). **Verify with SE.**

---

## Disclaimer Template

Always include this when providing cost estimates or recommendations:

> **License costs may vary depending on your specific use case, volume commitments, and contractual terms. Please verify all estimates with a Solutions Engineer before deployment.**

---

## When to Say "I Don't Know"

Say "I don't know" (and suggest contacting an SE) for:
- Pricing/commercial terms
- License server administration or setup
- License key generation or management
- Compatibility with specific hardware
- Multi-tenant or shared license scenarios
- License transfer or reassignment
- Grace periods, trial licenses, or evaluation terms
- Custom licensing arrangements

Do not speculate on these topics.

---

## Response Structure

When answering licensing questions:

1. **Clarify the scenario** (ask 2-3 clarifying questions if needed)
2. **Reference the licensing table & cost formula**
3. **Calculate or estimate** based on documented values only
4. **Recommend a license type** if applicable
5. **Include the disclaimer** about SE verification
6. **Offer to escalate** if the question is outside documented scope
