from fastapi import Header, HTTPException

from app.core.utils.auth_utils import check_authenticated


def ensure_authenticated(x_user_id: str = Header(None), x_user_role: str = Header(None)):
    check_authenticated(x_user_id, x_user_role)


def ensure_user_id(user_id: str, x_user_id: str = Header(None), x_user_role: str = Header(None)):
    check_authenticated(x_user_id, x_user_role)
    if x_user_id != user_id and x_user_role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")


def ensure_admin(x_user_id: str = Header(None), x_user_role: str = Header(None)):
    check_authenticated(x_user_id, x_user_role)
    if x_user_role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


def ensure_role(user_role: str, x_user_id: str = Header(None), x_user_role: str = Header(None)):
    check_authenticated(x_user_id, x_user_role)
    if x_user_role.lower() != user_role.lower():
        raise HTTPException(status_code=403, detail="Forbidden")
