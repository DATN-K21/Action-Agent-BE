import logging
import tempfile

from azure.storage.blob import BlobServiceClient
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

from app.core.settings import env_settings

logger = logging.getLogger(__name__)


def is_azure_blob_url(url: str) -> bool:
    """Check if the URL is an Azure blob storage URL."""
    return "blob.core.windows.net" in url


def download_azure_blob(blob_url: str) -> tuple[bytes, str]:
    """Download blob content using Azure SDK with authentication."""
    try:
        if not env_settings.AZURE_BLOB_CONNECTION_STRING:
            raise ValueError("Azure Blob Storage connection string not configured")

        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(env_settings.AZURE_BLOB_CONNECTION_STRING)

        # Parse blob URL to extract container and blob name
        # URL format: https://<account>.blob.core.windows.net/<container>/<blob>
        url_parts = blob_url.split("/")
        container_name = url_parts[-2]
        blob_name = url_parts[-1]

        # Get blob client and download
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        blob_data = blob_client.download_blob().readall()

        # Determine file extension from blob name
        file_extension = blob_name.split(".")[-1] if "." in blob_name else ""

        logger.info(f"Successfully downloaded Azure blob: {blob_name} ({len(blob_data)} bytes)")
        return blob_data, file_extension

    except Exception as e:
        logger.error(f"Failed to download Azure blob {blob_url}: {e}", exc_info=True)
        raise


def load_and_split_document(
    file_path: str,
    user_id: str,
    upload_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    logger.debug(f"Loading document from: {file_path}")

    # Only handle Azure blob URLs
    if not is_azure_blob_url(file_path):
        raise ValueError(f"Only Azure blob URLs are supported. Received: {file_path}")

    logger.info(f"Processing Azure blob URL: {file_path}")

    try:
        blob_data, file_extension = download_azure_blob(file_path)

        # Create temporary file with the downloaded content
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_file:
            temp_file.write(blob_data)
            temp_file_path = temp_file.name

        logger.debug(f"Created temporary file: {temp_file_path}")

        # Select the appropriate loader based on the file type
        if temp_file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(temp_file_path)
        elif temp_file_path.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(temp_file_path)
        elif temp_file_path.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(temp_file_path)
        elif temp_file_path.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(temp_file_path)
        elif temp_file_path.endswith(".txt"):
            loader = TextLoader(temp_file_path)
        elif temp_file_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(temp_file_path)
        elif temp_file_path.endswith(".md"):
            loader = UnstructuredMarkdownLoader(temp_file_path)
        else:
            raise ValueError(f"Unsupported file type: {temp_file_path}")

        documents = loader.load()
        logger.debug(f"Loaded {len(documents)} documents")

        # Clean up temporary file
        try:
            import os

            os.unlink(temp_file_path)
            logger.debug(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")

    except Exception as e:
        logger.error(f"Failed to process Azure blob: {e}")
        raise ValueError(f"Cannot access Azure blob storage: {e}")

    # Update document metadata
    for doc in documents:
        doc.metadata.update({"user_id": user_id, "upload_id": upload_id})

    # Text splitting
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.split_documents(documents)
    logger.debug(f"Split into {len(split_docs)} chunks")
    return split_docs
