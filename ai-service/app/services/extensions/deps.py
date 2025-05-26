# from functools import lru_cache
#
# from fastapi import Depends
#
# from app.services.extensions.extension_service_manager import ExtensionServiceManager
# from app.services.extensions.gmail_service import GmailService
# from app.services.extensions.google_calendar_service import GoogleCalendarService
# from app.services.extensions.google_maps_service import GoogleMapsService
# from app.services.extensions.google_meet_service import GoogleMeetService
# from app.services.extensions.googledrive_service import GoogleDriveService
# from app.services.extensions.notion_service import NotionService
# from app.services.extensions.outlook_service import OutlookService
# from app.services.extensions.slack_service import SlackService
# from app.services.extensions.youtube_service import YoutubeService
#
#
# @lru_cache()
# def get_gmail_service() -> GmailService:
#     return GmailService()
#
# @lru_cache()
# def get_google_calendar_service() -> GoogleCalendarService:
#     return GoogleCalendarService()
#
# @lru_cache()
# def get_google_meet_service() -> GoogleMeetService:
#     return GoogleMeetService()
#
# @lru_cache()
# def get_google_maps_service() -> GoogleMapsService:
#     return GoogleMapsService()
#
# @lru_cache()
# def get_youtube_service() -> YoutubeService:
#     return YoutubeService()
#
# @lru_cache()
# def get_slack_service() -> SlackService:
#     return SlackService()
#
# @lru_cache()
# def get_outlook_service() -> OutlookService:
#     return OutlookService()
#
# @lru_cache()
# def get_google_drive_service() -> GoogleDriveService:
#     return GoogleDriveService()
#
# @lru_cache()
# def get_notion_service() -> NotionService:
#     return NotionService()
#
# @lru_cache()
# def get_extension_service_manager(
#         gmail_service:GmailService = Depends(get_gmail_service),
#         google_calendar_service:GoogleCalendarService = Depends(get_google_calendar_service),
#         google_meet_service:GoogleMeetService = Depends(get_google_meet_service),
#         google_maps_service:GoogleMapsService = Depends(get_google_maps_service),
#         youtube_service:YoutubeService = Depends(get_youtube_service),
#         slack_service:SlackService = Depends(get_slack_service),
#         outlook_service:OutlookService = Depends(get_outlook_service),
#         google_drive_service:GoogleDriveService = Depends(get_google_drive_service),
#         notion_service:NotionService = Depends(get_notion_service),
# ) -> ExtensionServiceManager:
#     manager = ExtensionServiceManager()
#
#     # Register extension services
#     manager.register_extension_service(gmail_service)
#     manager.register_extension_service(google_calendar_service)
#     manager.register_extension_service(google_meet_service)
#     manager.register_extension_service(google_maps_service)
#     manager.register_extension_service(youtube_service)
#     manager.register_extension_service(slack_service)
#     manager.register_extension_service(outlook_service)
#     manager.register_extension_service(google_drive_service)
#     manager.register_extension_service(notion_service)
#
#
#     return manager
