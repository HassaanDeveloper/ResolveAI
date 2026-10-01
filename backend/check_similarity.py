from app.services.database import get_supabase_client
import json

client = get_supabase_client()

# Get stored embeddings
result = client.table('document_chunks').select('id, embedding').execute()
stored_embeddings = []
for c in result.data[:5]:
    emb = c['embedding']
    if isinstance(emb, str):
        emb = json.loads(emb)
    stored_embeddings.append(emb)

# Test query with actual stored embedding
query_emb = stored_embeddings[0]
print(f'Query embedding: first 5 = {query_emb[:5]}')

# Compute cosine similarity manually
import math

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot / (norm_a * norm_b)

for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    try:
        result = client.rpc('match_document_chunks', {
            'query_embedding': query_emb,
            'match_threshold': threshold,
            'match_count': 5
        }).execute()
        print(f'Threshold {threshold}: {len(result.data)} results')
    except Exception as e:
        print(f'Threshold {threshold}: error: {e}')