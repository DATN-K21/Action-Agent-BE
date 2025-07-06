# scripts/build_stubs.sh
#!/usr/bin/env bash
set -e
mkdir -p generated
python -m grpc_tools.protoc -I proto \
  --python_out=generated \
  --grpc_python_out=generated \
  proto/retrieval.proto
touch generated/__init__.py
echo "Stubs generated."
