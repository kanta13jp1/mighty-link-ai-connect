---
name: pdm-product-review
description: Execute rigorous Product Manager (PdM) review comparing the product against world-class hit B2B SaaS and AI products across 5 strategic pillars, generating actionable WBS enhancement plans.
triggers:
  - "pdm review"
  - "product review"
  - "saas audit"
  - "evaluate product"
license: Apache-2.0
metadata:
  version: v1
  publisher: mighty-link
---

# Product Manager (PdM) Review & Competitive Benchmarking Skill

This skill conducts deep product strategy, UX friction, and market fit audits by benchmarking against world-class B2B SaaS and AI leaders (Notion, Linear, Figma, Vercel, Claude, ChatGPT).

---

## 1. Five Strategic Evaluation Pillars

| Pillar | Focus Area & Questions to Answer | Benchmark Best Practices |
| :--- | :--- | :--- |
| **1. Value Proposition** | Is the primary benefit instantly understood within 5 seconds of landing on the page? | Linear: "The issue tracking tool you'll actually enjoy using." Direct, clear, zero jargon. |
| **2. Time-to-Value (TTV)** | How quickly can a new user see the "Aha!" moment without forced registration friction? | Interactive demo / sandboxed preview directly on the landing page before signup. |
| **3. UX Friction Reduction** | Are interactions fluid? Are micro-animations, keyboard shortcuts, and instant feedback implemented? | Figma/Notion: Instant local state updates, optimistic UI, buttery smooth transitions. |
| **4. Enterprise & Trust** | Are security posture, SOC2 compliance, data governance, and SLA commitments transparent? | Clear architecture diagrams, compliance badges, and data privacy disclosures. |
| **5. Growth & Viral Loops** | Are sharing hooks, embeddable widgets, or team collaboration features built-in? | Vercel preview links, shareable interactive reports, team invite triggers. |

---

## 2. Review Output Format

Generate structured audit reports highlighting immediate wins and WBS task proposals:

```markdown
### 🚀 Product Management (PdM) Audit Report

#### 1. Executive Summary & Product Score (0 - 100)
- **Strengths**: ...
- **Key Bottlenecks**: ...

#### 2. Pillar Analysis & Gap Breakdown
1. **Value Proposition**: [Passed / Needs Improvement]
2. **Time-to-Value & Onboarding**: ...
3. **UX & Micro-Interactions**: ...

#### 3. Actionable WBS Task Proposals (TXXX)
- `TXXX-1`: Implement interactive sandbox preview on Hero section.
- `TXXX-2`: Add zero-friction copy-to-clipboard demo export.
```
