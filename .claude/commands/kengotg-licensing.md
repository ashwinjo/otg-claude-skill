---
name: kengotg-licensing
description: Quick KENG licensing check and cost estimation (dispatches to keng-licensing-agent)
disable-model-invocation: false
allowed-tools: []
---

# Licensing — Quick License Check & Cost Estimation

Quickly determine which KENG/OTG license tier suits your needs and get cost estimates.

## Agent Dispatch (REQUIRED)

**This command MUST dispatch to the `keng-licensing-agent` subagent.**

Do NOT execute the skill directly. Instead, use the Agent tool:

```
Agent tool call:
  subagent_type: keng-licensing-agent
  prompt: <forward the user's licensing question and any arguments>
  description: "KENG licensing check"
```

The agent will invoke the `keng-licensing` skill internally, handle all licensing calculations, and return results.

**Hierarchy:** `/kengotg-licensing` (command) → `keng-licensing-agent` (agent) → `keng-licensing` (skill)

---

## Quick Start

Ask about licensing:

```
/licensing
What license do I need for 4×100GE ports with 8 BGP sessions?
```

Get recommendations and cost breakdown instantly.

---

## Usage Patterns

### Simple POC Setup
```
/licensing
2×100GE ports, 4 BGP sessions, POC evaluation
```

**Result:** Developer or Team tier recommendation + cost

### Production Setup
```
/licensing
8×100GE ports, 20 BGP + 10 OSPF sessions, production testing
```

**Result:** Team or System tier + cost comparison

### Complex Multi-Protocol
```
/licensing
4×100GE + 4×25GE ports
20 BGP sessions, 10 OSPF sessions, 5 LAGs
Production network lab
```

**Result:** Tier comparison + optimization suggestions

### Upgrade Path
```
/licensing
Currently on Team tier, planning to add 4 more 100GE ports
Will that require System tier upgrade?
```

**Result:** Capacity analysis + upgrade recommendation

---

## What You Get

✓ DPLU (Data Plane License Unit) cost
✓ CPLU (Control Plane License Unit) cost
✓ License tier recommendation
✓ Cost breakdown by tier
✓ Tier comparison table
✓ Upgrade path suggestions
✓ SE disclaimer on estimates

---

## Licensing Tiers

### Developer Tier
```
Capacity:    250 DPLU, 10 CPLU
Example:     2×100GE + 4 BGP = 204 DPLU + 4 CPLU
Cost:        ~$X/month (verify with SE)
Use:         POCs, demos, small labs
```

### Team Tier
```
Capacity:    1000 DPLU, 50 CPLU
Example:     8×100GE + 20 BGP + 10 OSPF = 800 DPLU + 30 CPLU
Cost:        ~$Y/month (verify with SE)
Use:         Production testing, multi-site labs
```

### System Tier
```
Capacity:    Unlimited
Example:     Unlimited ports and sessions
Cost:        ~$Z/month (verify with SE)
Use:         Enterprise, large-scale labs
```

---

## Cost Calculation Examples

### Example 1: Basic BGP Test
```
Input:   2×100GE ports, AS 65001/65002
DPLU:    2×100 = 200 DPLU
CPLU:    2 BGP sessions = 2 CPLU
Total:   200 DPLU + 2 CPLU
Tier:    Developer (250 DPLU, 10 CPLU) ✓ Fits
Cost:    Developer tier pricing
```

### Example 2: Multi-Protocol Lab
```
Input:   4×100GE, 8 BGP + 4 OSPF + 2 LAGs
DPLU:    4×100 = 400 DPLU
CPLU:    8 BGP + 4 OSPF + 2 LAG = 14 CPLU
Total:   400 DPLU + 14 CPLU
Tier:    Team (1000 DPLU, 50 CPLU) ✓ Fits
Cost:    Team tier pricing
```

### Example 3: High-Scale Enterprise
```
Input:   16×100GE, 50 BGP + 20 OSPF + 10 LAGs
DPLU:    16×100 = 1600 DPLU
CPLU:    50 BGP + 20 OSPF + 10 LAG = 80 CPLU
Total:   1600 DPLU + 80 CPLU
Tier:    Team (insufficient) → System (unlimited) ✓
Cost:    System tier pricing
```

---

## DPLU Calculation Formula

```
DPLU = Σ(port_speed_GE)

Examples:
  1×10GE  = 10 DPLU
  1×25GE  = 25 DPLU
  1×100GE = 100 DPLU

  4×100GE + 2×25GE = 400 + 50 = 450 DPLU
```

---

## CPLU Calculation Formula

```
CPLU = BGP_sessions + OSPF_sessions + ISIS_sessions + ... + (LAGs × 0.5)

Examples:
  4 BGP = 4 CPLU
  4 BGP + 2 OSPF = 6 CPLU
  4 BGP + 2 OSPF + 3 LAGs = 6 + 1.5 = 7.5 CPLU
```

---

## Cost Optimization Tips

**Reduce port count:**
- Start with 2-4 ports instead of 8
- Upgrade later as needed
- Cost savings: 50-75% initially

**Consolidate protocols:**
- Test multiple protocols on same ports
- Use LAGs instead of multiple ports
- Cost savings: 10-20%

**Shared infrastructure:**
- Multiple tests on same lab
- Reuse deployed ports
- Cost savings: 30-50%

---

## Upgrade Path Examples

**Starting at Developer:**
```
Developer (250 DPLU, 10 CPLU)
   ↓ (add 2×100GE ports)
Team (1000 DPLU, 50 CPLU)
   ↓ (add 8×100GE ports + more protocols)
System (unlimited)
```

**Cost comparison:**
```
Developer: $100/month × 6 months = $600 (limited capacity)
Team:      $250/month × 6 months = $1500 (sufficient for growth)
System:    $500/month × 6 months = $3000 (unlimited)
→ Recommendation: Start with Team if growing
```

---

## Important Notes

⚠️ **Estimates:** Costs are approximate and vary by region
⚠️ **Verification:** Confirm with Solutions Engineer before purchase
⚠️ **Complex Features:** Some features may require higher tier
⚠️ **Licensing Model:** Verify current KENG licensing model with SE
⚠️ **Seat Limits:** Check team seat allocation limits

---

## Next Steps

1. **Get cost estimate:** Run `/kengotg-licensing` with your requirements
2. **Review options:** Compare tiers and upgrade paths
3. **Contact SE:** Verify with Solutions Engineer before purchase
4. **Deploy:** Use `/kengotg-deploy-ixia` to set up infrastructure
5. **Test:** Use `/kengotg-otg-gen` and `/kengotg-snappi-script` to create tests

---

## See Also

- `/kengotg-show-skills` — Skill overview
- `/kengotg-deploy-ixia` — Deploy infrastructure
- `/kengotg-otg-gen` — Create OTG config
- `/kengotg-snappi-script` — Generate test script
- `/kengotg-examples` — Workflow examples
