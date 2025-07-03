#!/bin/bash

# Azure Blob Storage Upload Script
# Usage: ./test_azure_upload.sh <SAS_URL> <file_path>

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <SAS_URL> <file_path>"
    echo "Example: $0 'https://your-storage.blob.core.windows.net/container/blob?sas-token' '/path/to/your/file.txt'"
    exit 1
fi

# Get arguments
URL="$1"
FILE_PATH="$2"

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$FILE_PATH' does not exist."
    exit 1
fi

echo "Azure Blob Storage Upload"
echo "SAS URL: $URL"
echo "File: $FILE_PATH"
echo "File size: $(wc -c < "$FILE_PATH") bytes"
echo

# Step 1: Create the append blob (must be done first)
echo "Step 1: Creating append blob..."
echo "Command: curl -X PUT \"\$URL\" -H \"x-ms-blob-type: AppendBlob\" -H \"Content-Length: 0\" -v"
echo
curl -X PUT "$URL" \
  -H "x-ms-blob-type: AppendBlob" \
  -H "Content-Length: 0" \
  -v

echo
echo "----------------------------------------"
echo

# Step 2: Append the file data
echo "Step 2: Appending file data..."
echo "Command: curl -X PUT \"\$URL&comp=appendblock\" -H \"Content-Type: application/octet-stream\" --data-binary \"@\$FILE_PATH\" -v"
echo
curl -X PUT "$URL&comp=appendblock" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@$FILE_PATH" \
  -v

echo
echo "----------------------------------------"
echo

# Step 3: Verify the upload (optional - check blob properties)
echo "Step 3: Checking blob properties (optional)..."
echo "Command: curl -I \"\$URL\" -v"
echo
curl -I "$URL" -v

echo
echo "Upload test completed!"
echo
echo "If you see HTTP 201 (Created) for step 1 and HTTP 201 (Created) for step 2, the upload was successful!"
