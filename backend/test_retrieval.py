from app.rag.retrieval.service import retrieval_service
from app.rag.retrieval.models import RetrievalRequest
import asyncio

async def test():
    request = RetrievalRequest(
        query="What is the refund policy for delayed shipments?",
        max_results=5,
        similarity_threshold=0.6,
    )
    response = await retrieval_service.retrieve(request)
    print(f'Query: {response.query}')
    print(f'Total candidates: {response.total_candidates}')
    print(f'Evidence count: {len(response.evidence)}')
    for ev in response.evidence:
        print(f'  - {ev.document_name}: similarity={ev.relevance_score:.4f}, section={ev.section}')

asyncio.run(test())