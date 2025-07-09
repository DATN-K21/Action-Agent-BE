# Retrieval Service

A pure gRPC service for RAG-based document retrieval in the Action Agent ecosystem.

## Overview

The Retrieval Service is a dedicated gRPC microservice that handles all document search operations for the Action Agent platform. It provides efficient vector, fulltext, and hybrid search capabilities using PGVector.

## Features

- **Pure gRPC Service**: Efficient binary protocol for high-performance communication
- **Vector Search**: Semantic similarity search using OpenAI embeddings
- **Fulltext Search**: Traditional text-based search (currently fallback to vector)
- **Hybrid Search**: Combined approach (currently fallback to vector)
- **Minimal Architecture**: Single-purpose service focused on retrieval

## gRPC API

### Service Definition

```protobuf
service RetrievalService {
  rpc Search(SearchRequest) returns (SearchResponse);
}
```

### SearchRequest

```protobuf
message SearchRequest {
  string user_id = 1;
  string upload_id = 2;
  string query = 3;
  string search_type = 4;  // vector, fulltext, hybrid
  int32 top_k = 5;
  float score_threshold = 6;
}
```

### SearchResponse

```protobuf
message SearchResponse {
  repeated SearchResult results = 1;
  int32 total = 2;
  string query = 3;
  string search_type = 4;
}
```

## Environment Variables

- `DEBUG_SERVER`: Enable debug mode (default: False)
- `LOGGING_LOG_LEVEL`: Log level (default: INFO)
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `PGVECTOR_POSTGRES_URL_PATH`: PostgreSQL connection string
- `PGVECTOR_POSTGRES_SCHEMA`: Database schema name
- `PGVECTOR_COLLECTION`: Vector collection name
- `GRPC_PORT`: gRPC server port (default: 15601)

## Development

### Running Locally

```bash
# Install dependencies
uv sync

# Start the service (gRPC files are pre-generated)
python app/main.py
```

### Regenerating gRPC Files (if needed)

```bash
# Only needed if you modify the proto file
python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=app/grpc \
    --grpc_python_out=app/grpc \
    proto/retrieval.proto
```

### Docker

```bash
# Build the image
docker build -t retrieval-service .

# Run the container
docker run -p 15601:15601 retrieval-service
```

## Architecture

- **gRPC Server**: High-performance binary protocol
- **PGVector**: Vector database for similarity search
- **OpenAI Embeddings**: Text embeddings for semantic search
- **Structlog**: Structured logging

## Integration

The service is designed to be called by the AI Service via gRPC for all document retrieval operations.

```python
# Example usage from AI Service
import grpc
from app.grpc import retrieval_pb2, retrieval_pb2_grpc

with grpc.insecure_channel('localhost:15601') as channel:
    stub = retrieval_pb2_grpc.RetrievalServiceStub(channel)
    request = retrieval_pb2.SearchRequest(
        user_id="user123",
        upload_id="upload456",
        query="How to implement authentication?",
        search_type="vector",
        top_k=5,
        score_threshold=0.7
    )
    response = stub.Search(request)
```
