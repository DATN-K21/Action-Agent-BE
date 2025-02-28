from functools import lru_cache

from fastapi import Depends

from app.services.extensions.extension_service_manager import ExtensionServiceManager
from app.services.extensions.gmail_service import GmailService

@lru_cache()
def get_gmail_service() -> GmailService:
    return GmailService()

@lru_cache()
def get_extension_service_manager(
        gmail_service:GmailService = Depends(get_gmail_service)
) -> ExtensionServiceManager:
    manager = ExtensionServiceManager()

    # Register gmail extension service
    manager.register_extension_service(gmail_service)

    return manager