import sys

sys.path.append("./")

from app.core.rag.embeddings import get_embedding_model
from app.core.rag.pgvector import PGVectorWrapper

# Initialize PGVectorWrapper and embedding model
pgvector_store = PGVectorWrapper()
embedding_model = get_embedding_model("zhipuai")

# Define query text
query_text = "Automatic Control Technology Co., Ltd."

# Perform vector search (requires user_id and upload_ids)
# Replace these values with actual values from your system
user_id = 1  # Replace with actual user_id
upload_ids = [1, 2, 3]  # Replace with actual list of upload_ids

# Execute search using vector search method
results = pgvector_store.vector_search(
    user_id=user_id,
    upload_ids=upload_ids,
    query=query_text,
    top_k=5,
    score_threshold=0.5
)

# Print results
print(f"Found {len(results)} documents:")
for i, doc in enumerate(results):
    print(f"\n--- Document {i + 1} ---")
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
    print(f"Score: {doc.metadata.get('score', 'N/A')}")
