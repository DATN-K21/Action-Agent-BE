from functools import lru_cache

from fastapi import Depends

from app.services.extensions.extension_service_manager import ExtensionServiceManager
from app.services.extensions.gmail_service import GmailService
from app.services.extensions.google_calendar_service import GoogleCalendarService
from app.services.extensions.google_maps_service import GoogleMapsService
from app.services.extensions.google_meet_service import GoogleMeetService


@lru_cache()
def get_gmail_service() -> GmailService:
    return GmailService()

@lru_cache()
def get_google_calendar_service() -> GoogleCalendarService:
    return GoogleCalendarService()

@lru_cache()
def get_google_meet_service() -> GoogleMeetService:
    return GoogleMeetService()

@lru_cache()
def get_google_maps_service() -> GoogleMapsService:
    return GoogleMapsService()

@lru_cache()
def get_extension_service_manager(
        gmail_service:GmailService = Depends(get_gmail_service),
        google_calendar_service:GoogleCalendarService = Depends(get_google_calendar_service),
        google_meet_service:GoogleMeetService = Depends(get_google_meet_service),
        google_maps_service:GoogleMapsService = Depends(get_google_maps_service),
) -> ExtensionServiceManager:
    manager = ExtensionServiceManager()

    # Register extension services
    manager.register_extension_service(gmail_service)
    manager.register_extension_service(google_calendar_service)
    manager.register_extension_service(google_meet_service)
    manager.register_extension_service(google_maps_service)


    return manager
