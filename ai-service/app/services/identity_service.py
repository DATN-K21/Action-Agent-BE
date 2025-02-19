from fastapi import Request


class IdentityService:
    def __init__(self, request: Request):
        self.request = request

    def user_id(self) -> str:
        return self.request.headers.get("X-UserId", "")

    def user_name(self) -> str:
        return self.request.headers.get("X-Username", "")

    def user_email(self) -> str:
        return self.request.headers.get("X-Email", "")

    def user_role(self) -> str:
        return self.request.headers.get("X-Role", "")

    def is_admin(self) -> bool:
        return self.user_role() == "admin"

    def is_same_user(self, user_id: str) -> bool:
        return self.user_id() == user_id
