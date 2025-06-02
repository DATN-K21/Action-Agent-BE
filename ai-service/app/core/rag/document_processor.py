import logging

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

logger = logging.getLogger(__name__)


def load_and_split_document(
    file_path: str,
    user_id: int,
    upload_id: int,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    logger.debug(f"Loading document from: {file_path}")

    if file_path.startswith("http://") or file_path.startswith("https://"):
        loader = WebBaseLoader(web_path=file_path)
    else:
        # Select the appropriate loader based on the file type
        if file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(file_path)
        elif file_path.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(file_path)
        elif file_path.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(file_path)
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(file_path)
        elif file_path.endswith(".md"):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    logger.debug(f"Loaded {len(documents)} documents")

    # Update document metadata
    for doc in documents:
        doc.metadata.update({"user_id": user_id, "upload_id": upload_id})

    # Text splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    split_docs = text_splitter.split_documents(documents)
    logger.debug(f"Split into {len(split_docs)} chunks")
    return split_docs
