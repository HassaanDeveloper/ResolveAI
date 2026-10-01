from app.services.database import get_supabase_client

client = get_supabase_client()

# Check documents
result = client.table('documents').select('*').execute()
print(f'Documents: {len(result.data)}')
for d in result.data[:3]:
    print(f'  - {d["name"]}: id={d["id"]}')

# Check document_chunks
result = client.table('document_chunks').select('id, document_id, embedding').execute()
print(f'Chunks: {len(result.data)}')
for c in result.data[:3]:
    print(f'  - chunk_id: {c["id"]}, doc_id: {c["document_id"]}, embedding: {"yes" if c["embedding"] else "no"}')