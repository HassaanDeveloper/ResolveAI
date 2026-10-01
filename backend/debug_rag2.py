from app.services.database import get_supabase_client
from app.rag.embeddings import gemini_embedding_service
import asyncio

async def test():
    client = get_supabase_client()
    
    # Get a real embedding from the documents
    result = client.table('document_chunks').select('embedding').limit(1).execute()
    if result.data:
        emb = result.data[0]['embedding']
        if isinstance(emb, str):
            import json
            emb = json.loads(emb)
        print(f'Stored embedding dim: {len(emb)}')
        print(f'First 5 values: {emb[:5]}')
    
    # Test with a real query
    query = "What is the refund policy for delayed shipments?"
    embedding = await gemini_embedding_service.embed_query(query)
    print(f'Query embedding dim: {len(embedding)}')
    print(f'First 5 values: {embedding[:5]}')
    
    # Test search with real embedding
    client = get_supabase_client()
    try:
        result = client.rpc('match_document_chunks', {
            'query_embedding': embedding,
            'match_threshold': 0.1,
            'match_count': 5
        }).execute()
        print(f'match_document_chunks works: {len(result.data)} results')
        for r in result.data:
            print(f'  - {r["document_name"]}: similarity={r["similarity"]:.4f}')
    except Exception as e:
        print('match_document_chunks error:', e)

asyncio.run(test())