import typing

import composio
import composio.tools
from composio import Action
from composio.client.files import FileDownloadable
from composio.tools.toolset import FileIOHelper
from composio_langgraph import ComposioToolSet
from fastapi import APIRouter, Depends
from langchain_openai import ChatOpenAI

from app.api.deps import ensure_authenticated
from app.core.settings import env_settings
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


def monkey_patched(
    self,
    schema: typing.Dict,
    request: typing.Dict,
    action: Action,
    file_helper: FileIOHelper,
) -> typing.Dict:
    if "properties" not in schema:
        return request

    params = schema["properties"]
    for _param in request:
        if _param not in params:
            continue

        if self._file_downloadable(schema=params[_param]):
            request[_param] = str(FileDownloadable(**request[_param]).download(file_helper.outdir / action.app / action.slug))
            continue

        if isinstance(request[_param], dict) and params[_param].get("type") == "object":
            request[_param] = self._substitute_file_downloads_recursively(
                schema=params[_param],
                request=request[_param],
                action=action,
                file_helper=file_helper,
            )
            continue

    return request


def patch_lib():
    composio.tools.toolset.SchemaHelper._substitute_file_downloads_recursively = monkey_patched


@router.get("/test-call-slack", summary="Test call slack", response_model=ResponseWrapper)
def call_tool():
    patch_lib()

    composio_toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY, entity_id="abb8af82-2c47-42e3-9c82-b28705be12e4")
    tools = composio_toolset.get_tools(actions=[Action.SLACK_LIST_ALL_SLACK_TEAM_CHANNELS_WITH_VARIOUS_FILTERS])
    llm = ChatOpenAI(openai_api_key=env_settings.OPENAI_API_KEY)
    llm = llm.bind_tools(tools)
    task = "Help me to list all channels in this workspace"
    response = llm.invoke(task)
    print("[response]", response)

    if len(response.tool_calls) > 0:
        tool_call = response.tool_calls[0]
        args = tool_call["args"]
        print("[args]", args)
        result = tools[0].invoke(args)
        print("result", result)

    return ResponseWrapper.wrap(status=200, message="Success").to_response()