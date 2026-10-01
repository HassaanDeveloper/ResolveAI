from app.services.database import get_supabase_client

client = get_supabase_client()

# Test with very low threshold
for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    try:
        result = client.rpc('match_document_chunks', {
            'query_embedding': [0.1] * 3072,
            'match_threshold': threshold,
            'match_count': 5
        }).execute()
        print(f'Threshold {threshold}: {len(result.data)} results')
    except Exception as e:
        print(f'Threshold {threshold}: error: {e}')