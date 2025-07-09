"""
Fully Async Azure-blob → Document chunks
────────────────────────────────────────
• Downloads with `azure.storage.blob.aio` (non-blocking)
• Uses async file I/O with `aiofiles` (non-blocking)
• Uses `loader.aload()` when the LangChain loader supports it
  - otherwise falls back to `run_in_executor`.
• Runs CPU-intensive text splitting in thread pool (non-blocking)
• Keeps exactly the same return type: `list[Document]`
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import List, Sequence

import aiofiles
import aiofiles.os
from azure.storage.blob.aio import BlobServiceClient
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


async def _download_azure_blob_async(blob_url: str) -> tuple[bytes, str, str]:
    """Async download via Azure SDK (aio variant)."""
    if not env_settings.AZURE_BLOB_CONNECTION_STRING:
        raise ValueError("Azure Blob Storage connection string not configured")

    try:
        svc = BlobServiceClient.from_connection_string(env_settings.AZURE_BLOB_CONNECTION_STRING)
        parts = blob_url.split("/")
        container_name = parts[-2]
        blob_name = parts[-1]
        blob_client = svc.get_blob_client(container=container_name, blob=blob_name)

        stream = await blob_client.download_blob()
        blob_data: bytes = await stream.readall()

        filename = blob_name.split(".")[0] if "." in blob_name else blob_name
        ext = blob_name.split(".")[-1] if "." in blob_name else ""
        logger.info("Downloaded blob %s (%s bytes)", blob_name, len(blob_data))
        return blob_data, filename, ext
    finally:
        await svc.close()


async def _async_loader_docs(loader) -> Sequence[Document]:
    """
    Try async `.aload()` first;
    if not available, run sync `.load()` in thread-pool.
    """
    if hasattr(loader, "aload"):
        return await loader.aload()

    return await asyncio.get_running_loop().run_in_executor(None, loader.load)


# ───────────────────────── public API ──────────────────────
async def aload_and_split_document(
    file_path: str,
    user_id: str,
    upload_id: str,
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Document]:
    """Returns document chunks ready for embedding."""
    if "blob.core.windows.net" not in file_path:
        raise ValueError("Only Azure blob URLs are supported")

    blob_data, filename, ext = await _download_azure_blob_async(file_path)

    # 1. Write to a temp file (async)
    fd, temp_path = tempfile.mkstemp(prefix=f"{filename}_", suffix=f".{ext}")
    os.close(fd)  # Close the file descriptor so we can open it async

    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(blob_data)

    try:
        # 2. Pick loader by extension
        if temp_path.endswith(".pdf"):
            loader = PyMuPDFLoader(temp_path)
        elif temp_path.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(temp_path)
        elif temp_path.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(temp_path)
        elif temp_path.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(temp_path)
        elif temp_path.endswith(".txt"):
            loader = TextLoader(temp_path)
        elif temp_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(temp_path)
        elif temp_path.endswith(".md"):
            loader = UnstructuredMarkdownLoader(temp_path)
        else:
            raise ValueError(f"Unsupported file type: {temp_path}")

        # 3. Load pages (async when possible)
        documents = list(await _async_loader_docs(loader))
        logger.debug("Loaded %s pages from %s", len(documents), temp_path)

    finally:
        try:
            await aiofiles.os.remove(temp_path)
        except OSError:
            logger.warning("Failed to delete temp file %s", temp_path)

    # 4. Augment metadata
    for doc in documents:
        doc.metadata.update({"user_id": user_id, "upload_id": upload_id})

    # 5. Split into RAG-friendly chunks (CPU-bound, run in executor)
    loop = asyncio.get_running_loop()
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = await loop.run_in_executor(None, splitter.split_documents, documents)
    logger.debug("Split into %s chunks", len(split_docs))
    return split_docs
