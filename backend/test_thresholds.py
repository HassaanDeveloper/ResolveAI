from app.services.database import get_supabase_client

client = get_supabase_client()

# Test with different thresholds
for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    result = client.rpc('match_document_chunks', {
        'query_embedding': [0.1] * 3072,
        'match_threshold': threshold,
        'match_count': 5
    }).execute()
    
    print(f'Threshold {threshold}: {len(result.data)} results')
    for r in result.data:
        meta = r.get('metadata', {})
        if 'section' in meta:
            print(f'  Section: {meta["section"]}, similarity={r["similarity"]:.4f}')