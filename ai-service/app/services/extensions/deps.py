from app.services.extensions.extension_service_manager import ExtensionServiceManager
from app.services.extensions.gmail_service import GmailService


def get_extension_service_manager() -> ExtensionServiceManager:
    manager = ExtensionServiceManager()

    # Register gmail extension service
    gmail_service = GmailService()
    manager.register_extension_service(gmail_service)

    return manager