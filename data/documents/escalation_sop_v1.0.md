# Northstar Commerce Escalation Standard Operating Procedure
**Version:** 1.0  
**Effective Date:** 2025-03-01  
**Source:** internal-sop  
**Document ID:** ESCALATION-SOP-1.0

---

## 1. Purpose
Defines when and how customer issues are escalated to human operators for resolution.

---

## 2. Escalation Triggers

### 2.1 Mandatory Escalation (System-Enforced)
The following **always** require human operator review:

| Trigger | Description | Priority |
|---------|-------------|----------|
| Refund > $500 | Any refund request exceeding $500 | High |
| Legal threat | Customer mentions lawyer, lawsuit, legal action | Urgent |
| Regulatory inquiry | Government agency, BBB, consumer protection | Urgent |
| Media attention | Social media complaint going viral, press inquiry | Urgent |
| Policy ambiguity | Clear policy conflict or gap | High |
| VIP customer | Tier: Platinum, Diamond, Enterprise | High |
| Previous escalation | Same order/customer escalated before | High |
| Exception request | Customer requests policy exception | Medium |

### 2.2 Discretionary Escalation (Agent Judgment)
Agents may escalate when:
- Customer is visibly distressed or emotional
- Complex multi-order issue requiring coordination
- Technical issue beyond agent tools
- Customer explicitly requests supervisor

---

## 3. Escalation Process

### 3.1 Automated Escalation (System)
1. Workflow engine detects trigger
2. Creates escalation record with context
3. Assigns to next available Tier 2 operator
4. Notifies customer: "Your case has been escalated to a specialist. Expected response: 2 hours."

### 3.2 Manual Escalation (Agent)
1. Agent clicks "Escalate" in console
2. Fills required fields: reason, priority, customer impact
3. System creates escalation record
4. Routes to appropriate queue (refunds, cancellations, technical, VIP)

### 3.3 Escalation Queues
| Queue | Handles | SLA |
|-------|---------|-----|
| Refund Approvals | Refunds > $100, policy exceptions | 4 hours |
| Cancellation Review | Post-shipment cancellations | 4 hours |
| VIP Concierge | Platinum/Diamond/Enterprise | 1 hour |
| Legal/Compliance | Legal threats, regulatory | 2 hours |
| Technical | System issues, data problems | 8 hours |

---

## 4. Operator Responsibilities

### 4.1 Tier 2 Operator (Refund/Cancellation)
- Review case details and policy
- Approve, deny, or request additional info
- Document decision with policy citation
- Close escalation with resolution summary

### 4.2 Senior Operator (VIP/Legal)
- Handle high-risk/escalated cases
- Authorize exceptions with director notification
- Coordinate with legal/compliance if needed
- Ensure audit trail completeness

---

## 5. Escalation Data Requirements
Every escalation must include:
- Request ID and workflow ID
- Customer ID and tier
- Order ID (if applicable)
- Trigger reason (from Section 2)
- Priority level
- Customer communication history
- Policy citations reviewed
- Decision and rationale
- Operator ID and timestamp

---

## 6. De-escalation
- If resolved at Tier 2: Operator closes, customer notified
- If requires higher authority: Re-assign to Senior Operator with notes
- Customer may request re-escalation once if unsatisfied (goes to Senior)

---

## 7. Metrics & Reporting
Tracked weekly:
- Escalation volume by trigger type
- Average resolution time by queue
- Approval/denial rates
- Customer satisfaction (post-escalation survey)
- Repeat escalation rate

---

## 8. Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-03-01 | Operations | Initial SOP |