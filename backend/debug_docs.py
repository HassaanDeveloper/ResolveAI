from app.services.database import get_supabase_client

client = get_supabase_client()

# Check documents
result = client.table('documents').select('*').ilike('name', '%Test%').execute()
print(f'Documents: {len(result.data)}')
for d in result.data:
    print(f'  - {d["name"]} (status: {d["status"]})')

# Check chunks
result = client.table('document_chunks').select('id, document_id, content').ilike('metadata->>test_namespace', 'eval-test-%').execute()
print(f'Chunks: {len(result.data)}')
for c in result.data[:3]:
    print(f'  Chunk: {c["content"][:80]}...')