from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["Tests"], summary="Endpoint to check server.")
async def check():
    return {"message": "oke"}


@router.get("/error", tags=["Tests"], summary="Endpoint to check error handlers.")
def error():
    raise Exception("Test exception")
