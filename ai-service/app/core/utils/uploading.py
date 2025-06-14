"""API to deal with file uploads via a runnable.

For now this code assumes that the content is a base64 encoded string.

The details here might change in the future.

For the time being, upload and ingestion are coupled
"""

from __future__ import annotations

import mimetypes
from typing import BinaryIO, List, Optional

from fastapi import UploadFile
from langchain_community.document_loaders.parsers import BS4HTMLParser, PyMuPDFParser
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_core.documents.base import Blob
from langchain_core.runnables import ConfigurableField, RunnableConfig, RunnableSerializable
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from pydantic import ConfigDict, SecretStr

from app.core.settings import env_settings
from app.core.utils.ingesting import ingest_blob

HANDLERS = {
    "application/pdf": PyMuPDFParser(),
    "text/plain": TextParser(),
    "text/html": BS4HTMLParser(),
    "application/msword": MsWordParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (MsWordParser()),
}

SUPPORTED_MIMETYPES = sorted(HANDLERS.keys())

# PUBLIC API

MIMETYPE_BASED_PARSER = MimeTypeBasedParser(
    handlers=HANDLERS,
    fallback_parser=None,
)


def _guess_mimetype(file_name: str, file_bytes: bytes) -> str:
    """Guess the mime-type of a file based on its name or bytes."""
    # Guess based on the file extension
    mime_type, _ = mimetypes.guess_type(file_name)

    # Return detected mime type from mimetypes guess, unless it's None
    if mime_type:
        return mime_type

    # Signature-based detection for common types
    if file_bytes.startswith(b"%PDF"):
        return "application/pdf"
    elif file_bytes.startswith((b"\x50\x4b\x03\x04", b"\x50\x4b\x05\x06", b"\x50\x4b\x07\x08")):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_bytes.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/msword"
    elif file_bytes.startswith(b"\x09\x00\xff\x00\x06\x00"):
        return "application/vnd.ms-excel"

    # Check for CSV-like plain text content (commas, tabs, newlines)
    try:
        decoded = file_bytes[:1024].decode("utf-8", errors="ignore")
        if all(char in decoded for char in (",", "\n")) or all(char in decoded for char in ("\t", "\n")):
            return "text/csv"
        elif decoded.isprintable() or decoded == "":
            return "text/plain"
    except UnicodeDecodeError:
        pass

    return "application/octet-stream"


def convert_ingestion_input_to_blob(file: UploadFile) -> Blob:
    """Convert ingestion input to blob."""
    file_data = file.file.read()
    file_name = file.filename

    # Check if file_name is a valid string
    if not isinstance(file_name, str):
        raise TypeError(f"Expected string for file name, got {type(file_name)}")

    mimetype = _guess_mimetype(file_name, file_data)
    return Blob.from_data(
        data=file_data,
        path=file_name,
        mime_type=mimetype,
    )


class IngestRunnable(RunnableSerializable[BinaryIO, List[str]]):
    """Runnable for ingesting files into a vectorstore."""

    text_splitter: TextSplitter
    vectorstore: VectorStore
    assistant_id: Optional[str] = None
    thread_id: Optional[str] = None
    """Ingested documents will be associated with assistant_id or thread_id.
    
    ID is used as the namespace, and is filtered on at query time.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def namespace(self) -> str:
        if (self.assistant_id is None and self.thread_id is None) or (self.assistant_id is not None and self.thread_id is not None):
            raise ValueError("Exactly one of assistant_id or thread_id must be provided")
        return self.assistant_id if self.assistant_id is not None else self.thread_id  # type: ignore

    def invoke(self, blob: Blob, config: Optional[RunnableConfig] = None, **kwargs) -> List[str]:
        out = ingest_blob(
            blob,
            MIMETYPE_BASED_PARSER,
            self.text_splitter,
            self.vectorstore,
            self.namespace,
        )
        return out


PG_CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver="psycopg",
    host=env_settings.POSTGRES_HOST,
    port=env_settings.POSTGRES_PORT,
    database=env_settings.POSTGRES_DB,
    user=env_settings.POSTGRES_USER,
    password=env_settings.POSTGRES_PASSWORD,
)


def _get_openai_embeddings(async_mode: bool) -> PGVector:
    if env_settings.LLM_DEFAULT_API_KEY:
        return PGVector(
            OpenAIEmbeddings(openai_api_key=SecretStr(env_settings.LLM_DEFAULT_API_KEY)),  # type: ignore
            connection=PG_CONNECTION_STRING,
            use_jsonb=True,
            async_mode=async_mode,
        )

    raise ValueError("LLM_DEFAULT_API_KEY needs to be set for embeddings to work.")


vstore = _get_openai_embeddings(async_mode=True)

ingest_runnable = IngestRunnable(
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200),
    vectorstore=_get_openai_embeddings(async_mode=False),
).configurable_fields(
    thread_id=ConfigurableField(
        id="thread_id",
        annotation=Optional[str],
        name="Thread ID",
    ),
)
