import typing

import composio
from composio import Action
from composio.client.files import FileDownloadable
from composio.tools.toolset import FileIOHelper


def substitute_file_downloads_recursively(
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
            request[_param] = str(
                FileDownloadable(**request[_param]).download(file_helper.outdir / action.app / action.slug))
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


def patch_substitute_file_downloads_recursively():
    composio.tools.toolset.SchemaHelper._substitute_file_downloads_recursively = patch_substitute_file_downloads_recursively
