import httpx

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class AIServiceClient:
    """HTTP client for communicating with AI service to update upload status."""

    def __init__(self):
        self.base_url = env_settings.AI_SERVICE_URL.rstrip("/")
        self.timeout = 30.0

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        return headers

    async def update_upload_status(self, upload_id: str, status: str, error_message: str | None = None) -> bool:
        """Update upload status via AI service internal API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {"status": status, "error_message": error_message}

                response = await client.patch(
                    f"{self.base_url}/private/uploads/{upload_id}/status", json=payload, headers=self._get_headers()
                )

                if response.status_code == 200:
                    logger.info(f"Successfully updated upload {upload_id} status to {status}")
                    return True
                else:
                    logger.error(
                        f"Failed to update upload {upload_id} status. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False

        except httpx.RequestError as e:
            logger.error(f"Request error updating upload {upload_id} status: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating upload {upload_id} status: {e}")
            return False

    def update_upload_status_sync(self, upload_id: str, status: str, error_message: str | None = None) -> bool:
        """Synchronous version of update_upload_status."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {"status": status, "error_message": error_message}

                response = client.patch(
                    f"{self.base_url}/private/uploads/{upload_id}/status", json=payload, headers=self._get_headers()
                )

                if response.status_code == 200:
                    logger.info(f"Successfully updated upload {upload_id} status to {status}")
                    return True
                else:
                    logger.error(
                        f"Failed to update upload {upload_id} status. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False

        except httpx.RequestError as e:
            logger.error(f"Request error updating upload {upload_id} status: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating upload {upload_id} status: {e}")
            return False

    def delete_upload_record_sync(self, upload_id: str) -> bool:
        """Delete upload record via AI service internal API."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.delete(f"{self.base_url}/private/uploads/{upload_id}", headers=self._get_headers())

                if response.status_code == 200:
                    logger.info(f"Successfully deleted upload record {upload_id}")
                    return True
                else:
                    logger.error(
                        f"Failed to delete upload record {upload_id}. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False

        except httpx.RequestError as e:
            logger.error(f"Request error deleting upload record {upload_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting upload record {upload_id}: {e}")
            return False


# Global client instance
ai_service_client = AIServiceClient()
