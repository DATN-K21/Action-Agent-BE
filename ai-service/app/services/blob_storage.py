import uuid
from datetime import datetime, timedelta
from functools import lru_cache

from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient
from fastapi import UploadFile

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class BlobStorageService:
    """
    Thin async wrapper around Azure Blob Storage.
    """

    def __init__(self) -> None:
        if not env_settings.AZURE_BLOB_CONNECTION_STRING or not env_settings.AZURE_BLOB_CONTAINER_NAME:
            raise ValueError("Azure Blob Storage settings are not configured")
        self._client = BlobServiceClient.from_connection_string(env_settings.AZURE_BLOB_CONNECTION_STRING)
        self._container_client = self._client.get_container_client(env_settings.AZURE_BLOB_CONTAINER_NAME)

    async def upload_uploadfile(self, upload_file: UploadFile) -> str:
        """
        Stream an UploadFile directly to Blob.
        Returns **blob URL** – easier for downstream workers.
        """
        blob_name = f"{uuid.uuid4()}-{upload_file.filename}"
        blob_client = self._container_client.get_blob_client(blob_name)

        # make sure cursor at the beginning
        await upload_file.seek(0)

        try:
            await blob_client.upload_blob(
                data=upload_file.file,  # this is a SpooledTemporaryFile -> stream
                overwrite=True,
                content_settings=ContentSettings(content_type=upload_file.content_type or "application/octet-stream"),
            )
            logger.info(f"Uploaded {upload_file.filename} -> Azure blob {blob_name}")
            return blob_client.url  # return https://<account>.blob.core…
        except Exception as exc:
            logger.error(f"Blob upload failed: {exc}", exc_info=True)
            raise

    def generate_sas_url(self, blob_url: str, expiry_hours: int = 24) -> str:
        """
        Generate a SAS URL for temporary access to a blob.
        This is useful for Celery workers that need temporary access.
        """
        try:
            # Extract blob name from URL
            url_parts = blob_url.split("/")
            blob_name = url_parts[-1]

            # Parse connection string to get account name and key
            conn_parts = dict(part.split("=", 1) for part in env_settings.AZURE_BLOB_CONNECTION_STRING.split(";") if "=" in part)
            account_name = conn_parts.get("AccountName")
            account_key = conn_parts.get("AccountKey")

            if not account_name or not account_key:
                raise ValueError("Could not extract account credentials from connection string")

            if not env_settings.AZURE_BLOB_CONTAINER_NAME:
                raise ValueError("Azure Blob Storage container name is not configured")

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=env_settings.AZURE_BLOB_CONTAINER_NAME,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
            )

            # Return URL with SAS token
            sas_url = f"{blob_url}?{sas_token}"
            logger.info(f"Generated SAS URL for blob {blob_name}, expires in {expiry_hours} hours")
            return sas_url

        except Exception as e:
            logger.error(f"Failed to generate SAS URL for {blob_url}: {e}", exc_info=True)
            raise

    async def upload_uploadfile_with_sas(self, upload_file: UploadFile, expiry_hours: int = 24) -> str:
        """
        Upload file and return SAS URL for temporary access.
        This is better for Celery workers as they get temporary read access.
        """
        # Upload the file first
        blob_url = await self.upload_uploadfile(upload_file)

        # Generate SAS URL for temporary access
        sas_url = self.generate_sas_url(blob_url, expiry_hours)

        return sas_url


@lru_cache()
def get_blob_storage_service() -> BlobStorageService:
    return BlobStorageService()
