# Northstar Commerce Refund Approval Matrix
**Version:** 1.0  
**Effective Date:** 2025-01-15  
**Source:** internal-policy  
**Document ID:** REFUND-APPROVAL-MATRIX-1.0

---

## 1. Purpose
Defines approval authority levels for refund decisions based on amount and circumstances.

---

## 2. Approval Tiers

### Tier 1: Auto-Approve (System)
| Condition | Authority | Process |
|-----------|-----------|---------|
| Refund ≤ $100 AND eligibility met | System (automatic) | No human review |
| Carrier loss ≤ $100 | System | Auto-processed |
| Price adjustment ≤ $50 | System | Auto-processed |

### Tier 2: Manager Approval
| Condition | Authority | SLA |
|-----------|-----------|-----|
| Refund $100.01 - $500 | Refund Manager / Team Lead | 4 hours |
| Policy exception request (any amount) | Refund Manager | 4 hours |
| Post-shipment cancellation | Refund Manager | 4 hours |
| VIP customer exception | Refund Manager | 2 hours |

### Tier 3: Director Approval
| Condition | Authority | SLA |
|-----------|-----------|-----|
| Refund $500.01 - $1,000 | Director of Customer Experience | 8 hours |
| High-value customer (Enterprise tier) exception | Director | 4 hours |
| Media/social media escalation | Director | 2 hours |
| Regulatory inquiry response | Director + Legal | 24 hours |

### Tier 4: Legal Review
| Condition | Authority | SLA |
|-----------|-----------|-----|
| Refund > $1,000 | Legal Counsel + Director | 48 hours |
| Legal threat / lawsuit mention | Legal Counsel | 24 hours |
| Class action potential | Legal Counsel + VP | 48 hours |
| Data privacy / regulatory complaint | Legal Counsel + Compliance | 24 hours |

---

## 3. Approval Decision Options

| Decision | Description | Next Steps |
|----------|-------------|------------|
| **APPROVE** | Refund authorized per policy | Process immediately, notify customer |
| **APPROVE WITH CONDITIONS** | Approved with stipulations | Document conditions, process per conditions |
| **DENY** | Policy violation or insufficient evidence | Notify customer with policy citation, offer alternatives |
| **REQUEST MORE INFO** | Insufficient data to decide | Specify needed info, pause SLA until received |
| **ESCALATE UP** | Exceeds authority level | Forward to next tier with recommendation |

---

## 4. Approval Documentation Requirements
Every approval/denial must record:
- Approver ID, role, timestamp
- Refund amount, order ID, customer ID
- Policy sections applied
- Decision rationale (2-3 sentences)
- Conditions (if any)
- Escalation trail (if re-assigned)

---

## 5. Emergency Override
For urgent cases (legal threat, media crisis):
1. Director or VP may authorize verbally
2. Must be documented within 2 hours
3. Full review within 24 hours
3. Audit flag for compliance review

---

## 6. Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | Policy Team | Initial matrix aligned with Refund Policy v2.1 |