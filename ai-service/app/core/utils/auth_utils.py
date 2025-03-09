from fastapi import HTTPException


def check_authenticated(x_user_id: str, x_user_role: str):
    if not x_user_id or not x_user_role:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
