from fastapi import APIRouter

from app.schemas.base import ResponseWrapper

router = APIRouter(prefix="", tags=["Tests"], responses={})


@router.get("/ping", summary="Endpoint to check server.", response_model=dict)
async def check():
    return {"message": "pong"}


@router.get("/error", summary="Endpoint to check error handlers.", response_model=ResponseWrapper)
async def error():
    raise Exception("Test exception")