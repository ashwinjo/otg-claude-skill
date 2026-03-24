---
name: Licensing Integration into Snappi Script Generator
description: Design and implementation of keng-licensing skill integration into snappi-script-generator agent
type: project
---

## Overview

**Date:** 2026-03-24
**Task:** Integrate keng-licensing skill into snappi-script-generator agent
**Status:** ✅ Complete — Agent spec updated with licensing capability

## Implementation Details

### Agent Specification Changes

**File:** `.claude/agents/snappi-script-generator-agent.md`

**Changes Made:**

1. **Added keng-licensing to available skills**
   - Line 20-21: Added `- keng-licensing` to skills list
   - Agent can now invoke licensing analysis

2. **Updated Responsibilities (Primary)**
   - Added: "Analyze and report licensing requirements — Call keng-licensing skill to determine required licenses (KENG-SEAT, KENG-DPLU, KENG-CPLU) and estimated costs"
   - Added to Secondary: "Report licensing estimates and recommendations before test execution"

3. **Updated Output Format**
   - Added new `licensing_info` section with:
     - seats_required (e.g., 2)
     - seat_type (e.g., "KENG-SEAT")
     - data_plane_licenses array (port speed + count + license type + cost)
     - control_plane_licenses array (protocol + license type + sessions + cost)
     - total_estimated_annual_cost
     - disclaimer about cost estimates

4. **Updated Decision Tree**
   - Added "Analyze licensing requirements" step after script validation
   - Workflow: Extract test parameters → Call keng-licensing skill → Get licenses + costs → Include in output

5. **Updated Example Flow**
   - Added licensing analysis step: "Extract: 2 ports × 10Gbps + BGP protocol → Call keng-licensing skill → Get: KENG-SEAT (2) + KENG-DPLU-10G (2) + KENG-CPLU"
   - Returns: script + licensing info + execution instructions

6. **Updated Expected Output**
   - Added licensing block with visual formatting:
     ```
     💼 LICENSING REQUIREMENTS
     ├─ Seats: 2 × KENG-SEAT
     ├─ Data Plane: 2 × 10G KENG-DPLU-10G
     ├─ Control Plane: 1 × KENG-CPLU (BGP)
     └─ Annual Cost: ~$17,000 (verify with Solutions Engineer)
     ```

7. **Updated Success Criteria**
   - Added: "Licensing requirements analyzed and reported to user"
   - Added: "Licensing info includes seat count, license types, estimated annual cost, and disclaimer"

### Workflow (When Script is Generated)

1. **User provides:** OTG config + infrastructure YAML
2. **Agent reads:** OTG config to extract test parameters:
   - Port count and speeds
   - Protocol types (BGP, ISIS, LACP, etc.)
   - Protocol session counts
   - Test duration
3. **Agent invokes:** keng-licensing skill with test parameters
4. **Licensing skill returns:**
   - Required seat count
   - Required license types (KENG-SEAT, KENG-DPLU-*, KENG-CPLU, KENG-UNLIMITED-CP)
   - Estimated annual costs for each component
   - Disclaimer about cost accuracy
5. **Agent returns to user:**
   - ✅ Generated Snappi script
   - 💼 Licensing requirements breakdown
   - 🚀 Execution instructions
   - 📊 Cost estimates

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Call licensing AFTER script generation | Script is primary deliverable; licensing is secondary info |
| Include disclaimer in output | Emphasize that costs may vary; encourage verification with Solutions Engineer |
| Show breakdown by component | Users understand what licenses they need and why |
| Annual cost estimation | Helps with budgeting and procurement planning |
| Display in formatted block | Makes licensing info prominent and easy to scan |

## Example Output

```
✅ Snappi script generated: test_bgp_convergence.py
📋 Estimated runtime: 120 seconds
🔗 Controller: http://localhost:8443

💼 LICENSING REQUIREMENTS
├─ Seats: 2 × KENG-SEAT ($500/seat/year)
├─ Data Plane: 2 × 10G KENG-DPLU-10G ($5000/port/year)
├─ Control Plane: 1 × KENG-CPLU - BGP ($2000/year)
└─ Annual Cost: ~$17,000 (verify with Solutions Engineer)

🚀 Execute with: python test_bgp_convergence.py
📊 Output: JSON report with metrics
```

## Next Steps

1. **Test the integration:**
   - Invoke snappi-script-generator agent with a BGP test scenario
   - Verify it generates both script AND licensing info
   - Validate licensing calculations are accurate

2. **Document examples:**
   - Add to `.claude/commands/kengotg-create-test.md` showing licensing output
   - Include licensing in workflow examples

3. **User feedback:**
   - Monitor if licensing info is helpful for procurement/budgeting
   - Adjust format/detail based on user feedback

## Files Updated

- `.claude/agents/snappi-script-generator-agent.md` — Agent spec with licensing integration
- `.claude/memory/integration_licensing_snappi.md` — This file (design documentation)

## Related Skills & Agents

- **keng-licensing skill** — Provides licensing analysis
- **snappi-script-generator skill** — Generates Snappi scripts (unchanged)
- **snappi-script-generator-agent** — Orchestrates both (updated to include licensing)

## See Also

- `.claude/skills/snappi-script-generator/SKILL.md` — Updated with licensing documentation
- `.claude/skills/keng-licensing/SKILL.md` — Licensing calculation details
