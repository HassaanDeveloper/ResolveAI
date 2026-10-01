from app.services.database import get_supabase_client
from app.rag.embeddings import gemini_embedding_service
from app.rag.retrieval.service import retrieval_service
from app.rag.retrieval.models import RetrievalRequest
import asyncio
import json

async def test():
    client = get_supabase_client()
    
    # Get actual stored embedding from our test document
    result = client.table('document_chunks').select('embedding').limit(1).execute()
    if result.data:
        emb = result.data[0]['embedding']
        if isinstance(emb, str):
            emb = json.loads(emb)
        print(f'Stored embedding dim: {len(emb)}, first 5: {emb[:5]}')
    
    # Test with actual query from rag_001
    query = "What is the refund policy for delayed shipments?"
    embedding = await gemini_embedding_service.embed_query(query)
    print(f'Query embedding dim: {len(embedding)}, first 5: {embedding[:5]}')
    
    # Test with different thresholds
    for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8]:
        try:
            result = client.rpc('match_document_chunks', {
                'query_embedding': embedding,
                'match_threshold': threshold,
                'match_count': 5
            }).execute()
            print(f'Threshold {threshold}: {len(result.data)} results')
            if result.data:
                for r in result.data[:2]:
                    print(f'  - {r["document_name"]}: similarity={r["similarity"]:.4f}')
        except Exception as e:
            print(f'Threshold {threshold}: error: {e}')

asyncio.run(test())