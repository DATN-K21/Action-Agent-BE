from functools import lru_cache

from fastapi import Request


class IdentityService:
    def __init__(self, request: Request):
        self.request = request

    def user_id(self) -> str:
        return self.request.headers.get("X-UserId", "").lower()

    def user_name(self) -> str:
        return self.request.headers.get("X-Username", "").lower()

    def user_email(self) -> str:
        return self.request.headers.get("X-Email", "").lower()

    def user_role(self) -> str:
        return self.request.headers.get("X-Role", "").lower()

    def is_admin(self) -> bool:
        return self.user_role() == "admin"

    def is_same_user(self, user_id: str) -> bool:
        return self.user_id() == user_id.lower()


@lru_cache()
def get_identity_service(request: Request):
    return IdentityService(request)