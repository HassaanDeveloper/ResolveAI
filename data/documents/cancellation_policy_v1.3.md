# Northstar Commerce Order Cancellation Policy
**Version:** 1.3  
**Effective Date:** 2025-02-01  
**Source:** internal-policy  
**Document ID:** CANCELLATION-POLICY-1.3

---

## 1. Purpose
Defines the conditions under which customers may cancel orders and the associated processes.

---

## 2. Cancellation Windows

### 2.1 Before Shipment (AUTO_APPROVE)
- Orders in **pending** or **processing** status may be cancelled at any time before shipment
- No approval required
- Full refund to original payment method
- Cancellation confirmed immediately

### 2.2 After Shipment (REQUIRES_APPROVAL)
Once an order has shipped (status: **shipped**, **in_transit**, **delivered**):
- Standard cancellation **not permitted** through self-service
- Customer must request **escalation** to human operator
- If shipment is **delayed > 14 business days** past estimated delivery:
  - Cancellation may be approved with return authorization
  - Customer must agree to refuse delivery or return item upon receipt
- If shipment is **not delayed**: Customer must refuse delivery or initiate standard return after receipt

---

## 3. Cancellation Process

### 3.1 Customer-Initiated
1. Customer requests cancellation via support channel
2. System checks order and shipment status
3. If before shipment → auto-cancel, confirm to customer
4. If after shipment → create escalation, inform customer of options

### 3.2 System-Initiated
- Fraud detection: Immediate cancellation, notification to customer
- Inventory unavailable: Cancellation with apology and alternative options
- Payment failure: 48-hour grace period, then cancellation

---

## 4. Post-Shipment Cancellation Options

| Shipment Status | Option | Requirements |
|-----------------|--------|--------------|
| in_transit, delayed ≤ 14 days | Refuse delivery | Customer refuses package, return to sender |
| delayed > 14 days | Cancellation + return auth | Manager approval, customer agrees to return |
| delivered | Standard return | 30-day return window, item in original condition |

---

## 5. Refunds for Cancelled Orders
- Before shipment: Full refund to original payment method
- After shipment (refused): Refund upon carrier scan of return
- After shipment (returned): Refund upon warehouse receipt and inspection

---

## 6. Exceptions
- **VIP customers:** May receive exception for post-shipment cancellation (director approval)
- **High-value orders (> $1000):** Always require director approval for post-shipment cancellation
- **Custom/personalized items:** Cannot be cancelled once production started

---

## 7. Audit Trail
All cancellations logged with:
- Order ID, customer ID, request timestamp
- Order/shipment status at time of request
- Approval chain (if applicable)
- Final outcome and refund amount

---

## 8. Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2023-03-01 | Policy Team | Initial version |
| 1.1 | 2023-09-15 | Policy Team | Added delay exception |
| 1.2 | 2024-06-01 | Policy Team | Clarified refusal vs return |
| 1.3 | 2025-02-01 | Policy Team | Updated approval matrix reference |