import uuid
from datetime import datetime, timedelta
from functools import lru_cache

from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class BlobStorageService:
    """
    Thin async wrapper around Azure Blob Storage.
    """

    def __init__(self) -> None:
        # Validate Azure Blob Storage configuration
        if not env_settings.AZURE_BLOB_CONNECTION_STRING or env_settings.AZURE_BLOB_CONNECTION_STRING == "<your-connection-string>":
            raise ValueError("Azure Blob Storage connection string is not configured")
        if not env_settings.AZURE_BLOB_CONTAINER_NAME or env_settings.AZURE_BLOB_CONTAINER_NAME == "<your-container-name>":
            raise ValueError("Azure Blob Storage container name is not configured")

        # Validate connection string format
        if "AccountName=" not in env_settings.AZURE_BLOB_CONNECTION_STRING or "AccountKey=" not in env_settings.AZURE_BLOB_CONNECTION_STRING:
            raise ValueError("Azure Blob Storage connection string is malformed - missing AccountName or AccountKey")

        try:
            self._client = BlobServiceClient.from_connection_string(env_settings.AZURE_BLOB_CONNECTION_STRING)
            self._container_client = self._client.get_container_client(env_settings.AZURE_BLOB_CONTAINER_NAME)
        except Exception as e:
            raise ValueError(f"Failed to initialize Azure Blob Storage client: {e}") from e

    def generate_sas_url(self, blob_url: str, expiry_hours: int = 1) -> str:
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

    async def delete_blob(self, blob_url: str) -> bool:
        """
        Delete a blob from Azure Blob Storage.

        Args:
            blob_url: The full URL of the blob to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Extract blob name from URL
            url_parts = blob_url.split("/")
            blob_name = url_parts[-1]

            # Remove SAS token if present
            if "?" in blob_name:
                blob_name = blob_name.split("?")[0]

            blob_client = self._container_client.get_blob_client(blob_name)

            # Check if blob exists before attempting deletion
            blob_exists = await blob_client.exists()
            if not blob_exists:
                logger.warning(f"Blob {blob_name} does not exist, skipping deletion")
                return False

            # Delete the blob
            await blob_client.delete_blob()
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True

        except Exception as exc:
            logger.error(f"Failed to delete blob {blob_url}: {exc}", exc_info=True)
            return False

    async def generate_append_blob_sas(self, filename: str, expiry_hours: int = 1, max_file_size_mb: int = 100) -> dict[str, str | int]:
        """
        Generate a SAS URL for direct client upload to an append blob using account key authentication.
        This allows streaming uploads and better handling of large files.

        Note: This method uses account key authentication instead of user delegation keys (AAD)
        to avoid "Only authentication scheme Bearer is supported" errors when the Azure Storage
        account is configured for AAD-only access but we're using connection string auth.

        Args:
            filename: The original filename (will be prefixed with UUID)
            expiry_hours: How long the SAS should be valid (default 1 hour)
            max_file_size_mb: Maximum file size in MB (default 100MB)

        Returns:
            dict with 'upload_url' (SAS URL for append operations), 'blob_url' (final public URL), and size limits
        """
        try:
            # Generate unique blob name
            blob_name = f"{uuid.uuid4()}-{filename}"
            blob_client = self._container_client.get_blob_client(blob_name)

            # Parse connection string to get account name and key
            conn_parts = dict(part.split("=", 1) for part in env_settings.AZURE_BLOB_CONNECTION_STRING.split(";") if "=" in part)
            account_name = conn_parts.get("AccountName")
            account_key = conn_parts.get("AccountKey")

            if not account_name or not account_key:
                raise ValueError("Could not extract account credentials from connection string")

            # Generate SAS token for append blob operations (create, write permissions)
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)

            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=env_settings.AZURE_BLOB_CONTAINER_NAME,
                blob_name=blob_name,
                account_key=account_key,  # Use account key instead of user delegation key
                permission=BlobSasPermissions(read=True, write=True, create=True),
                expiry=expiry_time,
            )

            # Construct URLs
            upload_url = f"{blob_client.url}?{sas_token}"
            blob_url = blob_client.url  # Public URL without SAS
            max_size_bytes = max_file_size_mb * 1024 * 1024  # Convert MB to bytes

            logger.info(f"Generated append blob SAS for {filename} -> {blob_name}, expires in {expiry_hours} hours, max size: {max_file_size_mb}MB")

            return {
                "upload_url": upload_url,  # Frontend uses this for append operations
                "blob_url": blob_url,  # Store this in DB for future reference
                "blob_name": blob_name,  # Optional: for tracking
                "expires_at": expiry_time.isoformat(),
                "max_file_size_mb": max_file_size_mb,
                "max_file_size_bytes": max_size_bytes,
            }

        except Exception as exc:
            logger.error(f"Failed to generate append blob SAS for {filename}: {exc}", exc_info=True)
            raise

    async def check_blob_status(self, blob_url: str, max_file_size_mb: int = 100) -> dict[str, str | int | bool | float]:
        """
        Check the status of a blob - whether it exists, its size, and if it's complete.

        Args:
            blob_url: The blob URL to check
            max_file_size_mb: Maximum allowed file size in MB

        Returns:
            dict with status information: exists, size_bytes, size_mb, within_limits, complete
        """
        try:
            # Extract blob name from URL
            url_parts = blob_url.split("/")
            blob_name = url_parts[-1]

            blob_client = self._container_client.get_blob_client(blob_name)
            max_size_bytes = max_file_size_mb * 1024 * 1024

            # Check if blob exists
            if await blob_client.exists():
                properties = await blob_client.get_blob_properties()
                size_bytes = properties.size
                size_mb = round(size_bytes / (1024 * 1024), 2)
                within_limits = size_bytes <= max_size_bytes
                complete = size_bytes > 0  # Consider non-empty blobs as complete

                logger.info(f"Blob status for {blob_name}: {size_bytes} bytes, within limits: {within_limits}")

                return {
                    "exists": True,
                    "size_bytes": size_bytes,
                    "size_mb": size_mb,
                    "within_limits": within_limits,
                    "complete": complete,
                    "max_size_mb": max_file_size_mb,
                    "max_size_bytes": max_size_bytes,
                }
            else:
                logger.info(f"Blob {blob_name} does not exist")
                return {
                    "exists": False,
                    "size_bytes": 0,
                    "size_mb": 0,
                    "within_limits": True,
                    "complete": False,
                    "max_size_mb": max_file_size_mb,
                    "max_size_bytes": max_size_bytes,
                }

        except Exception as exc:
            logger.error(f"Failed to check blob status for {blob_url}: {exc}", exc_info=True)
            return {
                "exists": False,
                "size_bytes": 0,
                "size_mb": 0,
                "within_limits": False,
                "complete": False,
                "error": str(exc),
                "max_size_mb": max_file_size_mb,
                "max_size_bytes": max_size_bytes,
            }


@lru_cache()
def get_blob_storage_service() -> BlobStorageService:
    return BlobStorageService()
