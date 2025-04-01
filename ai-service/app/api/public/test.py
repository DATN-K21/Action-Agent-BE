from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import ensure_authenticated
from app.schemas.base import ResponseWrapper
from app.services.mcps.demo_mcp import make_graph

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


class MCPRequest(BaseModel):
    input: str


@router.post("/mcp/chat", summary="Endpoint to check mcp chat.", response_model=ResponseWrapper)
async def mcp_chat(
        request: MCPRequest
):
    agent = make_graph()
    async with agent as agent:
        async for chunk in agent.astream({"messages": request.input}):
            print(chunk)

    return ResponseWrapper.wrap(status=200, message="Success").to_response()
