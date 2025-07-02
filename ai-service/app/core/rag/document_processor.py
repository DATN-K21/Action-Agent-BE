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
    WebBaseLoader,
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

    # Handle Azure blob URLs
    if is_azure_blob_url(file_path):
        logger.info(f"Detected Azure blob URL: {file_path}")

        try:
            blob_data, file_extension = download_azure_blob(file_path)

            # Create temporary file with the downloaded content
            with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_file:
                temp_file.write(blob_data)
                temp_file_path = temp_file.name

            # Use the temporary file path for loading
            actual_file_path = temp_file_path
            logger.debug(f"Created temporary file: {actual_file_path}")

        except Exception as e:
            logger.error(f"Failed to process Azure blob: {e}")
            raise ValueError(f"Cannot access Azure blob storage: {e}")

    elif file_path.startswith("http://") or file_path.startswith("https://"):
        # Handle regular web URLs
        loader = WebBaseLoader(web_path=file_path)
        documents = loader.load()
        logger.debug(f"Loaded {len(documents)} documents from web URL")
    else:
        # Handle local file paths
        actual_file_path = file_path

    # Load document based on file type (for local files and Azure blobs)
    if not (file_path.startswith("http://") or file_path.startswith("https://")) or is_azure_blob_url(file_path):
        # Select the appropriate loader based on the file type
        if actual_file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(actual_file_path)
        elif actual_file_path.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(actual_file_path)
        elif actual_file_path.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(actual_file_path)
        elif actual_file_path.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(actual_file_path)
        elif actual_file_path.endswith(".txt"):
            loader = TextLoader(actual_file_path)
        elif actual_file_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(actual_file_path)
        elif actual_file_path.endswith(".md"):
            loader = UnstructuredMarkdownLoader(actual_file_path)
        else:
            raise ValueError(f"Unsupported file type: {actual_file_path}")

        documents = loader.load()
        logger.debug(f"Loaded {len(documents)} documents")

        # Clean up temporary file if it was created
        if is_azure_blob_url(file_path):
            try:
                import os

                os.unlink(actual_file_path)
                logger.debug(f"Cleaned up temporary file: {actual_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")

    # Update document metadata
    for doc in documents:
        doc.metadata.update({"user_id": user_id, "upload_id": upload_id})

    # Text splitting
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = text_splitter.split_documents(documents)
    logger.debug(f"Split into {len(split_docs)} chunks")
    return split_docs
