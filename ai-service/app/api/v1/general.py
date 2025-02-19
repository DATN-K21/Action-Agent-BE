from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["General"], description="Endpoint to check server.")
async def check():
    return {"message": "oke"}
