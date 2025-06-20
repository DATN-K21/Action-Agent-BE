import json

from socketio import AsyncNamespace

from app.core import logging
from app.core.agents.agent import Agent
from app.core.graph.extension_builder_manager import ExtensionBuilderManager
from app.core.utils.convert_dict_message import convert_dict_message_to_message, convert_dict_message_to_output, \
    convert_dict_message_to_tool_calls
from app.core.utils.socket_decorate import validate_event
from app.core.utils.streaming import LanggraphNodeEnum, to_sse
from app.schemas.extension import SocketioExtensionCallback, SocketioExtensionRequest, ExtensionResponse
from app.services.extensions.extension_service_manager import ExtensionServiceManager

logger = logging.get_logger(__name__)


# noinspection PyMethodMayBeStatic,DuplicatedCode
class ExtensionNamespace(AsyncNamespace):
    def __init__(
            self,
            namespace: str,
            builder_manager: ExtensionBuilderManager,
            extension_service_manager: ExtensionServiceManager
    ):
        super().__init__(namespace=namespace)
        self.builder_manager = builder_manager
        self.extension_service_manager = extension_service_manager
        self.session_extension_to_agent = {}
        self.session_to_timezone = {}

    async def on_connect(self, sid, environ):
        tz = environ.get("HTTP_TIMEZONE", "Asia/Ho_Chi_Minh")  # Default to Asia/Ho_Chi_Minh if missing
        self.session_to_timezone[sid] = tz
        logger.info(f"Connected: {sid} with timezone: {tz}")

    async def on_disconnect(self, sid):
        logger.info(f"Disconnected: {sid}")
        if sid in self.session_extension_to_agent:
            self.session_extension_to_agent[sid] = {
                key: value for key, value in self.session_extension_to_agent.items() if key[0] != sid
            }
            del self.session_to_timezone[sid]

    async def on_set_timezone(self, sid, timezone):
        """Receive and store the timezone from the frontend."""
        self.session_to_timezone[sid] = timezone
        logger.info(f"User {sid} set timezone: {timezone}")

    async def on_message(self, sid, data):
        logger.info(f"Session {sid} sent a message: {data}")
        await self.emit("message", "hello", to=sid)

    def _check_exist_agent(self, sid, extension_name):
        if (sid, extension_name) not in self.session_extension_to_agent:
            return False

        return True

    def _create_agent(self, extension_name, user_id):
        extension_service = self.extension_service_manager.get_extension_service(extension_name)
        self.builder_manager.update_builder_tools(
            builder_name=extension_name,
            tools=extension_service.get_authed_tools(user_id),  # type: ignore
        )

        builder = self.builder_manager.get_extension_builder(extension_name)

        if builder is None:
            logger.error("Builder not found")
            return None

        graph = builder.build_graph(perform_action=True, has_human_acceptance_flow=True)
        return Agent(graph)

    @validate_event(SocketioExtensionCallback)
    async def on_handle_chat_interrupt(self, sid, data: SocketioExtensionCallback):
        if not self._check_exist_agent(sid, data.extension_name):
            logger.error("Agent not found")
            await self.emit("error", "Agent not found", to=sid)
            return

        agent = self.session_extension_to_agent[(sid, data.extension_name)]

        execute = data.execute
        tool_calls = data.tool_calls
        result = await agent.async_handle_chat_interrupt(
            execute=execute,
            tool_calls=tool_calls,
            thread_id=data.thread_id,
            timezone=self.session_to_timezone[sid],
            recursion_limit=data.recursion_limit if data.recursion_limit is not None else 10,
        )

        if execute:
            await self.emit(
                event="chat_interrupt",
                data=ExtensionResponse(
                    user_id=data.user_id,
                    thread_id=data.thread_id,
                    extension_name=data.extension_name,
                    interrupted=False,
                    output=result.output
                ).model_dump(),
                to=sid
            )

    @validate_event(SocketioExtensionRequest)
    async def on_chat(self, sid, data: SocketioExtensionRequest):
        try:
            if not self._check_exist_agent(sid, data.extension_name):
                agent = self._create_agent(data.extension_name, data.user_id)
                self.session_extension_to_agent[(sid, data.extension_name)] = agent

            agent = self.session_extension_to_agent[(sid, data.extension_name)]

            response = await agent.async_chat(
                question=data.input,
                thread_id=data.thread_id,
                timezone=self.session_to_timezone[sid],
                recursion_limit=data.recursion_limit if data.recursion_limit is not None else 10,
            )

            # emit response to the client
            await self.emit(
                event="chat_response",
                data=ExtensionResponse(
                    user_id=data.user_id,
                    thread_id=data.thread_id,
                    extension_name=data.extension_name,
                    interrupted=response.interrupted,
                    output=response.output
                ).model_dump(),
                to=sid
            )
        except Exception as e:
            logger.error(f"Error in chat event of extension namespace: {str(e)}", exc_info=True)
            await self.emit("error", "Internal server error", to=sid)

    @validate_event(SocketioExtensionCallback)
    async def on_handle_stream_interrupt(self, sid, data: SocketioExtensionCallback):
        if not self._check_exist_agent(sid, data.extension_name):
            logger.error("Agent not found")
            await self.emit("error", "Agent not found", to=sid)
            return

        agent = self.session_extension_to_agent[(sid, data.extension_name)]

        execute = data.execute
        tool_calls = data.tool_calls
        result = await agent.async_handle_stream_interrupt(
            execute=execute,
            tool_calls=tool_calls,
            thread_id=data.thread_id,
            timezone=self.session_to_timezone[sid],
            recursion_limit=data.recursion_limit if data.recursion_limit is not None else 10,
        )

        if execute:
            async for dict_message in to_sse(result):
                if dict_message.get("event") == "end":
                    await self.emit(
                        event="stream_interrupt",
                        data=ExtensionResponse(
                            user_id=data.user_id,
                            thread_id=data.thread_id,
                            extension_name=data.extension_name,
                            interrupted=False,
                            streaming=False,
                            output="",
                        ).model_dump(),
                        to=sid
                    )
                    return

                output = convert_dict_message_to_output(dict_message)
                if output is not None:
                    await self.emit(
                        event="stream_interrupt",
                        data=ExtensionResponse(
                            user_id=data.user_id,
                            thread_id=data.thread_id,
                            extension_name=data.extension_name,
                            interrupted=False,
                            streaming=True,
                            output=output
                        ).model_dump(),
                        to=sid
                    )

    @validate_event(SocketioExtensionRequest)
    async def on_stream(self, sid, data):
        try:
            if not self._check_exist_agent(sid, data.extension_name):
                agent = self._create_agent(data.extension_name, data.user_id)
                self.session_extension_to_agent[(sid, data.extension_name)] = agent

            agent = self.session_extension_to_agent[(sid, data.extension_name)]

            response = await agent.async_stream(
                question=data.input,
                thread_id=data.thread_id,
                timezone=self.session_to_timezone[sid],
                recursion_limit=data.recursion_limit if data.recursion_limit is not None else 10,
            )

            interrupted = False
            async for dict_message in to_sse(response):
                if dict_message.get("event") == "metadata":
                    dict_message_data = json.loads(dict_message.get("data"))
                    if dict_message_data["langgraph_node"] == LanggraphNodeEnum.HUMAN_EDITING_NODE:
                        interrupted = True
                elif interrupted:
                    tool_calls = convert_dict_message_to_tool_calls(dict_message)
                    if tool_calls is not None:
                        await self.emit(
                            event="stream_response",
                            data=ExtensionResponse(
                                user_id=data.user_id,
                                thread_id=data.thread_id,
                                extension_name=data.extension_name,
                                interrupted=True,
                                streaming=True,
                                output=tool_calls
                            ).model_dump(),
                            to=sid
                        )
                else:
                    message = convert_dict_message_to_message(dict_message)
                    if message is not None:
                        await self.emit(
                            event="stream_response",
                            data=ExtensionResponse(
                                user_id=data.user_id,
                                thread_id=data.thread_id,
                                extension_name=data.extension_name,
                                interrupted=False,
                                streaming=True,
                                output=message
                            ).model_dump(),
                            to=sid
                        )

                if dict_message.get("event") == "end":
                    await self.emit(
                        event="stream_response",
                        data=ExtensionResponse(
                            user_id=data.user_id,
                            thread_id=data.thread_id,
                            extension_name=data.extension_name,
                            interrupted=interrupted,
                            streaming=False,
                            output="",
                        ).model_dump(),
                        to=sid
                    )
                    return

        except Exception as e:
            logger.error(f"Error executing Extension API: {str(e)}", exc_info=True)
            await self.emit("error", "Internal server error", to=sid)
