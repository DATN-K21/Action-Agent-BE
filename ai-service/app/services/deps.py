from functools import lru_cache
from fastapi import  Request

from app.services.identity_service import IdentityService

@lru_cache()
# Identity Dependencies
def get_identity_service(request: Request):
    return IdentityService(request)