from fastapi import Header, HTTPException


class AuthContext:
    def __init__(self, x_user_id: str = Header(None), x_user_role: str = Header(None)):
        if not x_user_id or not x_user_role:
            raise HTTPException(status_code=401, detail="Unauthorized")
        self.user_id = x_user_id
        self.role = x_user_role

    def ensure_admin(self):
        if self.role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")

    def ensure_user_id(self, user_id: str):
        if self.user_id != user_id and self.role != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")

    def ensure_role(self, role: str):
        if self.role != role:
            raise HTTPException(status_code=403, detail="Forbidden")
