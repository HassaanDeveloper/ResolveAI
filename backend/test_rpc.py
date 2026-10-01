from app.services.database import get_supabase_client

client = get_supabase_client()

result = client.rpc('match_document_chunks', {
    'query_embedding': [0.1] * 3072,
    'match_threshold': 0.6,
    'match_count': 5
}).execute()

print(f'Results: {len(result.data)}')
for r in result.data:
    meta = r.get('metadata', {})
    if 'section' in meta:
        print(f'Section: {meta["section"]}, similarity={r["similarity"]:.4f}')