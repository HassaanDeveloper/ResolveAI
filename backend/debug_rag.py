from app.services.database import get_supabase_client
from app.rag.embeddings import gemini_embedding_service
import asyncio

async def test():
    from app.services.database import get_supabase_client
    client = get_supabase_client()
    
    # Test with actual query embedding from RAG
    query = "What is the refund policy for delayed shipments?"
    
    # First check what embeddings are stored
    from app.services.database import get_supabase_client
    client = get_supabase_client()
    
    result = client.table('document_chunks').select('id, embedding').limit(3).execute()
    for c in result.data[:3]:
        emb = c['embedding']
        if isinstance(emb, str):
            import json
            emb = json.loads(emb)
        print(f'Chunk {c["id"][:8]}: dim={len(emb)}, first5={emb[:5]}')
    
    # Test with actual query embedding
    import asyncio
    from app.rag.embeddings import gemini_embedding_service
    embedding = await gemini_embedding_service.embed_query("What is the refund policy for delayed shipments?")
    print(f'Query embedding dim: {len(embedding)}, first 5: {embedding[:5]}')
    
    # Test with real query embedding
    for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        result = client.rpc('match_document_chunks', {
            'query_embedding': embedding,
            'match_threshold': threshold,
            'match_count': 5
        }).execute()
        
        print(f'Threshold {threshold}: {len(result.data)} results')
        for r in result.data:
            meta = r.get('metadata', {})
            if 'section' in meta:
                print(f'  Section: {meta["section"]}, similarity={r["similarity"]:.4f}')

import asyncio
import json
asyncio.run(test())