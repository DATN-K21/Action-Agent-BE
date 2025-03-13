from fastapi import APIRouter, Depends

from app.api.deps import ensure_authenticated
from app.schemas.base import ResponseWrapper

router = APIRouter(prefix="", tags=["Tests"], responses={})


@router.get("/", summary="Endpoint to check server.", response_model=dict)
async def check():
    return {"message": "oke"}


@router.get("/error", summary="Endpoint to check error handlers.", response_model=ResponseWrapper)
async def error():
    raise Exception("Test exception")


@router.get("/auth", summary="Endpoint to check auth.", response_model=ResponseWrapper)
async def auth(
        _: bool = Depends(ensure_authenticated),
):
    return ResponseWrapper.wrap(status=200, message="Authenticated").to_response()
