from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["Tests"], description="Endpoint to check server.")
async def check():
    return {"message": "oke"}


@router.get("/error", tags=["Tests"], description="Endpoint to check error handlers.")
def error():
    raise Exception("Test exception")
