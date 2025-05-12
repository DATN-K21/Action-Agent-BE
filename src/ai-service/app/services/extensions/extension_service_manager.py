from typing import Sequence

from app.services.extensions.extension_service import ExtensionService


class ExtensionServiceManager:
    def __init__(self):
        self.extension_services = {}

    def register_extension_service(self, extension_service: ExtensionService):
        if extension_service.get_name() in self.extension_services:
            raise ValueError(f"Extension Service '{extension_service.get_name()} already exists")

        self.extension_services[extension_service.get_name()] = extension_service

    def remove_extension_service(self, name: str):
        if name not in self.extension_services:
            raise ValueError(f"Extension Service '{name}' does not exist")

        del self.extension_services[name]

    def get_extension_service(self, name: str) -> ExtensionService | None:
        if name not in self.extension_services:
            return None

        return self.extension_services[name]

    def get_all_extension_services(self) -> Sequence[ExtensionService]:
        return list(self.extension_services.values())

    def get_all_extension_service_names(self) -> list[str]:
        return list(self.extension_services.keys())
