from app.services.database import get_supabase_client
from app.rag.ingestion import ingestion_service
from app.rag.models import Document, DocumentSource
import asyncio

async def reingest():
    # Delete existing test documents
    client = get_supabase_client()
    client.table('documents').delete().like('name', '%Test Refund Policy%').execute()
    client.table('documents').delete().like('name', '%Test Cancellation%').execute()
    client.table('document_chunks').delete().like('metadata->>test_namespace', 'eval-test-%').execute()
    
    # Re-ingest with correct 3072-dim embeddings
    refund_doc = Document(
        name='Test Refund Policy for Integration Evaluation',
        source='test-policy',
        version='1.0',
        content='''# Test Refund Policy for Integration Evaluation
**Version:** 1.0  
**Effective Date:** 2025-09-10  
**Source:** test-policy  
**Document ID:** TEST-REFUND-POLICY-1.0

---

## 1. Test Delayed Shipment Refunds

### 1.1 Eligibility
Customers are eligible for a full refund if:
- Shipment is delayed beyond the estimated delivery date by more than **7 business days**
- Package has **not been delivered** (tracking shows in_transit, delayed, or failed)
- Customer has not received the item

### 1.2 Auto-Approval Threshold
- Refunds **<= $50** for delayed shipments: **AUTO_APPROVE**
- Refunds **> $50** for delayed shipments: **REQUIRES_APPROVAL** from test-manager

### 1.3 Process
1. Customer requests refund citing delayed shipment
2. System verifies tracking shows delay > 7 business days past estimated delivery
3. If eligible amount <= $50 -> automatic approval and processing
4. If eligible amount > $50 -> escalated to test-manager for approval

---

## 2. Test Carrier Loss or Damage

### 2.1 Eligibility
Full refund (including shipping costs) when:
- Carrier tracking shows "lost," "damaged," or "returned to sender"
- Carrier claim has been filed by Test Commerce logistics team
- Customer confirms non-receipt or damage upon delivery

### 2.2 Approval
- All carrier loss/damage refunds: **REQUIRES_APPROVAL** from test-manager
- Amounts > $200: **REQUIRES_APPROVAL** from test-director

---

## 3. Test Refund Approval Matrix

| Tier | Amount Range | Eligibility Met | Approval Required |
|------|--------------|-----------------|-------------------|
| 1 (Auto) | <= $50 | Yes | None (automatic) |
| 2 (Manager) | $50.01 - $200 | Yes | Test-manager approval |
| 3 (Director) | $200.01 - $500 | Yes | Test-director approval |
| 4 (Legal) | > $500 | Yes | Legal review required |
| Any | Any | No | **DENY** (policy violation) |

---

## 4. Test Non-Refundable Items
The following are not eligible for refund:
- Digital goods (software licenses, gift cards, subscriptions)
- Personalized/customized items (unless defective)
- Final sale / clearance items (marked as such at purchase)
- Items damaged by customer misuse
''',
        metadata={'test_namespace': 'eval-test-'}
    )
    
    result = await ingestion_service.ingest_document(refund_doc)
    print(f'Refund doc: {result.success}, chunks: {result.chunks_created}')
    
    # Cancellation policy
    cancel_doc = Document(
        name='Test Cancellation Policy for Integration Evaluation',
        source='test-policy',
        version='1.0',
        content='''# Test Cancellation Policy for Integration Evaluation
**Version:** 1.0  
**Effective Date:** 2025-09-10  
**Source:** test-policy  
**Document ID:** TEST-CANCELLATION-POLICY-1.0

---

## 1. Test Before Shipment
Cancellation before shipment is **ALLOWED** automatically.

---

## 2. Test After Shipment
Cancellation after shipment **REQUIRES_APPROVAL** from test-manager.

---

## 3. Test Delivered Orders
Cancellation for delivered orders is **DENIED**.
''',
        metadata={'test_namespace': 'eval-test-'}
    )
    
    result = await ingestion_service.ingest_document(cancel_doc)
    print(f'Cancel doc: {result.success}, chunks: {result.chunks_created}')

if __name__ == '__main__':
    asyncio.run(reingest())