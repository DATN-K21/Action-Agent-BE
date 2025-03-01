from functools import lru_cache

from fastapi import Depends

from app.services.extensions.extension_service_manager import ExtensionServiceManager
from app.services.extensions.gmail_service import GmailService
from app.services.extensions.google_calendar_service import GoogleCalendarService

@lru_cache()
def get_gmail_service() -> GmailService:
    return GmailService()

@lru_cache()
def get_google_calendar_service() -> GoogleCalendarService:
    return GoogleCalendarService()

@lru_cache()
def get_extension_service_manager(
        gmail_service:GmailService = Depends(get_gmail_service),
        google_calendar_service:GoogleCalendarService = Depends(get_google_calendar_service),
) -> ExtensionServiceManager:
    manager = ExtensionServiceManager()

    # Register extension services
    manager.register_extension_service(gmail_service)
    manager.register_extension_service(google_calendar_service)


    return manager