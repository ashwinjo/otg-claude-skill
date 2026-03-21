---
name: kengotg-check-licensing
description: Licensing evaluation workflow
disable-model-invocation: false
allowed-tools: []
---

# Check-Licensing — Licensing Evaluation Workflow

Complete licensing workflow: analyze requirements, get cost estimate, review recommendations, compare tiers.

## Quick Start

Evaluate licensing for your test infrastructure:

```
/kengotg-check-licensing
4×100GE ports with 8 BGP sessions, production testing
```

Get cost estimates, tier recommendations, and detailed analysis.

---

## Workflow Overview

```
Step 1: Analyze Requirements
├─ Parse port count and speeds
├─ Count protocol sessions
├─ Identify use case (POC, prod, etc.)
└─ Validate feasibility

       ↓

Step 2: Calculate Costs
├─ DPLU cost (port speeds)
├─ CPLU cost (protocol sessions)
├─ Total per tier (Dev, Team, System)
└─ Include disclaimers

       ↓

Step 3: Compare Tiers
├─ Developer tier (250 DPLU, 10 CPLU)
├─ Team tier (1000 DPLU, 50 CPLU)
├─ System tier (unlimited)
└─ Highlight best fit

       ↓

Step 4: Recommend & Optimize
├─ Primary recommendation
├─ Alternative options
├─ Cost savings suggestions
└─ Upgrade path analysis

       ↓

Complete: Cost Plan Ready!
```

---

## Input: Test Requirements

### Simple (2 parameters)
```
/kengotg-check-licensing
2×100GE, 4 BGP sessions
```

### Standard (3-4 parameters)
```
/kengotg-check-licensing
4×100GE + 2×25GE ports
8 BGP + 4 OSPF sessions
Production network lab
```

### Complex (5+ parameters)
```
/kengotg-check-licensing
8×100GE + 4×25GE ports
20 BGP + 10 OSPF + 5 ISIS sessions
5 LAGs
Multi-site enterprise lab
3-year commitment
```

---

## Example Scenarios

### Scenario 1: POC (Small Scale)
```
Input:
- 2×100GE ports
- 4 BGP sessions
- Use: Proof of concept
- Duration: 6 months

Analysis:
DPLU: 200 (2×100)
CPLU: 4 (4×BGP)
Total: 200 DPLU + 4 CPLU

Recommendation: Developer Tier
- Capacity: 250 DPLU, 10 CPLU ✓ Fits
- Cost: ~$100/month × 6 = $600
- Risk: None (plenty of headroom)
```

### Scenario 2: Production (Medium Scale)
```
Input:
- 8×100GE ports
- 20 BGP + 10 OSPF + 2 LAG sessions
- Use: Production testing lab
- Duration: 12 months

Analysis:
DPLU: 800 (8×100)
CPLU: 32 (20+10+2)
Total: 800 DPLU + 32 CPLU

Recommendation: Team Tier
- Capacity: 1000 DPLU, 50 CPLU ✓ Fits well
- Cost: ~$250/month × 12 = $3000
- Headroom: 200 DPLU, 18 CPLU (future growth)
```

### Scenario 3: Enterprise (High Scale)
```
Input:
- 16×100GE ports
- 50 BGP + 20 OSPF + 10 ISIS sessions
- 10 LAGs
- Use: Multi-site lab
- Duration: 36 months

Analysis:
DPLU: 1600 (16×100)
CPLU: 80 (50+20+10+5)
Total: 1600 DPLU + 80 CPLU

Recommendation: System Tier
- Capacity: Unlimited ✓ Fits
- Cost: ~$500/month × 36 = $18,000
- Note: System tier recommended for enterprise scale
```

---

## Workflow Steps

### Step 1: Input Requirements
```
/kengotg-check-licensing
[your port count, protocols, use case]
```

### Step 2: Receive Analysis
```
Cost Analysis Report
===================
DPLU Cost: 400 units
CPLU Cost: 14 units

Tier Comparison:
┌─────────────┬──────────┬──────────┬──────────┐
│ Tier        │ DPLU Cap │ CPLU Cap │ Fits?    │
├─────────────┼──────────┼──────────┼──────────┤
│ Developer   │ 250      │ 10       │ ✗ NO     │
│ Team        │ 1000     │ 50       │ ✓ YES    │
│ System      │ ∞        │ ∞        │ ✓ YES    │
└─────────────┴──────────┴──────────┴──────────┘

Recommended: Team Tier
```

### Step 3: Review Recommendations
```
Primary Recommendation: Team Tier
├─ Sufficient capacity for current needs
├─ Budget-friendly for 1-2 year commitment
├─ Headroom for 20% growth
└─ Cost: ~$250/month

Alternative: System Tier
├─ Unlimited capacity
├─ Future-proof (no upgrades)
├─ Higher cost (~$500/month)
└─ Consider if planning 50%+ growth
```

### Step 4: Get Optimization Tips
```
Cost Optimization Suggestions
────────────────────────────
1. Start with Team tier
   → Estimated cost: $3000/year

2. Defer 4 ports to phase 2
   → Save: $400/year
   → Still 75% capacity utilization

3. Consider annual commitment
   → Save: 10% discount
   → Total: $2700/year (estimated)
```

---

## Cost Calculation Reference

### DPLU (Data Plane License Units)
```
Based on port speeds:
  1×10GE   = 10 DPLU
  1×25GE   = 25 DPLU
  1×40GE   = 40 DPLU
  1×100GE  = 100 DPLU

Example:
  4×100GE + 2×25GE = (4×100) + (2×25)
                    = 400 + 50
                    = 450 DPLU
```

### CPLU (Control Plane License Units)
```
Based on protocol sessions:
  1×BGP session    = 1 CPLU
  1×OSPF session   = 1 CPLU
  1×ISIS session   = 1 CPLU
  1×LAG/LAG member = 0.5 CPLU

Example:
  4 BGP + 2 OSPF + 2 LAGs = 4 + 2 + (2×0.5)
                           = 4 + 2 + 1
                           = 7 CPLU
```

---

## Tier Details

### Developer Tier
```
Capacity:     250 DPLU, 10 CPLU
Cost:         ~$100/month
Best For:     POC, demos, small labs
Typical:      2-4 ports, minimal protocols
Upgrade Path: → Team tier
```

### Team Tier
```
Capacity:     1000 DPLU, 50 CPLU
Cost:         ~$250/month
Best For:     Production testing, multi-site labs
Typical:      8-20 ports, multiple protocols
Upgrade Path: → System tier (or co-exist)
```

### System Tier
```
Capacity:     Unlimited
Cost:         ~$500/month
Best For:     Enterprise, large-scale labs
Typical:      50+ ports, complex protocols
Upgrade Path: Enterprise support included
```

---

## Optimization Strategies

### Strategy 1: Phased Approach
```
Phase 1 (Months 1-6): Developer tier
├─ 2×100GE, 4 BGP
├─ Cost: $600
└─ Validate use case

Phase 2 (Months 7-18): Team tier
├─ Add 6 more ports
├─ Total: 8×100GE
└─ Cost: $3000

Total (18 months): $3600 saved vs upfront Team
```

### Strategy 2: Consolidation
```
Before: 4 separate labs
├─ Lab 1: 2 ports (Dev tier)
├─ Lab 2: 4 ports (Dev tier)
├─ Lab 3: 8 ports (Team tier)
└─ Lab 4: 4 ports (Dev tier)
Total: $4500/month

After: 1 shared lab
├─ Single 18-port Team tier lab
├─ Reuse across all tests
└─ Total: $250/month
Savings: 94% ($4250/month)
```

### Strategy 3: Multi-Year Commitment
```
Annual Commitment:
├─ 10% discount
├─ Team tier: $250 × 12 × 0.9 = $2700/year

3-Year Commitment:
├─ 20% discount
├─ Team tier: $250 × 36 × 0.8 = $7200
├─ Per-month average: $200
└─ Annual savings: $600
```

---

## Important Disclaimers

⚠️ **Costs are estimates** — Actual pricing may vary by region
⚠️ **Verify with SE** — Always confirm with Solutions Engineer before purchase
⚠️ **Complex features** — Some advanced features may require higher tier
⚠️ **Licensing model** — Verify current model (may change)
⚠️ **Seat limits** — Check team seat allocation limits

---

## Decision Matrix

```
How many ports do you need?

0-4 ports?
└─ Developer Tier ✓
   Start here for evaluation

5-20 ports?
└─ Team Tier ✓
   Perfect for production labs

20+ ports?
└─ System Tier ✓
   Enterprise scale

Unsure? Compare costs below:

2×100GE   = Developer Tier (200 DPLU < 250)
4×100GE   = Team Tier (400 DPLU > 250)
8×100GE   = Team Tier (800 DPLU < 1000)
16×100GE  = System Tier (1600 DPLU > 1000)
```

---

## What to Expect

### Output 1: Cost Analysis
- DPLU total, CPLU total
- Cost per tier
- Tier recommendation

### Output 2: Tier Comparison
- Feature matrix (all tiers)
- Capacity fit analysis
- Cost-benefit analysis

### Output 3: Recommendations
- Primary recommendation
- Alternative options
- Cost optimization suggestions
- Upgrade path

### Output 4: Next Steps
- How to purchase
- SE contact information
- Trial/PoC options
- License management

---

## Next Steps

1. **Input requirements:** Port count, protocols, use case
2. **Review analysis:** Check costs and recommendations
3. **Compare tiers:** Understand trade-offs
4. **Optimize:** Apply cost suggestions
5. **Contact SE:** Verify and purchase
6. **Deploy:** Use `/kengotg-create-test` to build tests

---

## Related Commands

- `/kengotg-create-test` — Full test creation pipeline
- `/kengotg-quick-bgp-test` — Quick BGP test
- `/kengotg-migrate-and-run` — Migration + execution
- `/kengotg-licensing` — Quick licensing check (single query)

---

## Tips

- **Plan ahead:** Get licensing sorted before infrastructure deployment
- **Document:** Keep cost analysis for budgeting
- **Optimize:** Review annually for cost savings
- **Grow gradually:** Phase in higher tiers as needs grow
- **Ask SE:** Don't hesitate to contact Solutions Engineer for guidance

---

## FAQ

**Q: Can I upgrade/downgrade during my commitment?**
A: Ask your Solutions Engineer about flexibility options.

**Q: What if my needs grow beyond my tier?**
A: Upgrade path options available; talk to SE.

**Q: Are there academic/startup discounts?**
A: Possible; contact SE with your use case.

**Q: Can I use multiple licenses together?**
A: Yes; ask about multi-seat/multi-lab options.

**Q: What's included in System tier?**
A: Unlimited capacity + premium support; confirm with SE.
