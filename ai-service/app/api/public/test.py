from fastapi import APIRouter, Depends
from langchain_core.tools import tool

from app.api.deps import ensure_authenticated
from app.schemas.base import ResponseWrapper
from app.services.model_service import AIModelService, AIModelProviderEnum

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


@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b


@router.get("/test-gpt4free", summary="Endpoint to check GPT4FREE.", response_model=ResponseWrapper)
async def test_gpt4free():
    tools = [add, multiply]
    model = AIModelService.get_ai_model(provider=AIModelProviderEnum.GPT4FREE)
    model.bind_functions(tools)
    res = await model.ainvoke("what is 2 + 4 using add tool")
    return ResponseWrapper.wrap(status=200, message=f"{res}").to_response()
