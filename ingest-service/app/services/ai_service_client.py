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

    def update_upload_status(self, upload_id: str, status: str, error_message: str | None = None) -> bool:
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


# Global client instance
ai_service_client = AIServiceClient()
