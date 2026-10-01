# Northstar Commerce Customer Service Standard Operating Procedure
**Version:** 2.0  
**Effective Date:** 2025-02-15  
**Source:** internal-sop  
**Document ID:** CS-SOP-2.0

---

## 1. Purpose
Standardizes customer service interactions for consistent, policy-compliant resolutions.

---

## 2. Service Principles
1. **Policy-first:** Every decision grounded in documented policy
2. **Transparency:** Explain the "why" behind decisions
3. **Empathy:** Acknowledge customer frustration before solving
4. **Efficiency:** Resolve at lowest tier possible
5. **Auditability:** Every interaction logged and traceable

---

## 3. Interaction Flow

### 3.1 Greeting & Verification
- Greet customer by name (from account)
- Verify identity: order number OR email + last 4 of payment method
- Acknowledge issue: "I understand you're concerned about [issue]"

### 3.2 Investigation
- Pull order details (order number, status, shipment)
- Check refund/cancellation history
- Review prior interactions (notes, escalations)

### 3.3 Policy Application
- Identify applicable policy document(s)
- Apply policy rules to customer's specific situation
- Determine: ALLOW / DENY / REQUIRES_APPROVAL

### 3.4 Communication
- **ALLOW:** "Good news — I can process that for you right now."
- **DENY:** "Unfortunately, policy doesn't allow this because [specific section]. Here's what I *can* do..."
- **REQUIRES_APPROVAL:** "This requires manager approval. I've escalated it. You'll hear back within [SLA]."

### 3.5 Closing
- Summarize action taken
- Provide reference/case number
- Set expectations for next steps
- "Is there anything else I can help with?"

---

## 4. Refund Eligibility Criteria (Quick Reference)

| Scenario | Eligible? | Policy Ref |
|----------|-----------|------------|
| Delayed > 7 biz days, not delivered | Yes (full) | Refund Policy §4 |
| Delivered ≤ 30 days, original condition | Yes | Refund Policy §3.1 |
| Delivered > 30 days | No (unless defective) | Refund Policy §3.1 |
| Defective item | Yes (no time limit) | Refund Policy §3.2 |
| Carrier lost/damaged | Yes (full + shipping) | Refund Policy §5 |
| Changed mind, shipped | No (escalation only) | Cancellation Policy §2.2 |
| Digital goods | No | Refund Policy §8 |
| Final sale items | No | Refund Policy §8 |

---

## 5. Prohibited Actions
- ❌ Promise refunds outside policy
- ❌ Bypass approval requirements
- ❌ Share internal policy documents with customers
- ❌ Delete or modify audit logs
- ❌ Process refund without operation_id (idempotency)
- ❌ Use personal judgment over policy rules

---

## 6. Required Documentation Per Interaction
Every customer interaction must log:
- Timestamp, agent ID, channel (chat/phone/email)
- Customer ID, order ID (if applicable)
- Issue category (refund, cancellation, shipping, other)
- Policy sections referenced
- Decision: ALLOW/DENY/ESCALATED
- If escalated: escalation ID, reason, priority
- Customer sentiment (satisfied/neutral/frustrated)
- Follow-up required (Y/N)

---

## 7. Quality Assurance
- Random audit: 10% of interactions weekly
- Metrics: First-contact resolution, policy compliance, CSAT
- Calibration sessions: Monthly with team leads
- Coaching: Based on audit findings

---

## 8. Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2023-01-15 | CS Leadership | Initial SOP |
| 1.5 | 2024-03-01 | CS Leadership | Added refund quick reference |
| 2.0 | 2025-02-15 | CS Leadership | Added prohibited actions, QA section |