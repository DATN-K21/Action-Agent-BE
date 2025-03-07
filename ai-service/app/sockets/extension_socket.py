from socketio import AsyncNamespace

from app.core import logging
from app.core.agents.agent import Agent
from app.core.graph.extension_builder_manager import ExtensionBuilderManager
from app.core.utils.convert_dict_message import convert_dict_message_to_binary_score, convert_dict_message_to_tool_call, \
    convert_dict_message_to_message
from app.core.utils.socket_decorate import validate_event
from app.schemas.extension import ExtensionCallBack, ExtensionRequest, ExtensionResponse
from app.services.extensions.extension_service_manager import ExtensionServiceManager
from app.utils.enums import HumanAction
from app.utils.streaming import to_sse

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

    async def on_connect(self, sid, environ):
        logger.info(f"Connected: {sid}")

    async def on_disconnect(self, sid):
        logger.info(f"Disconnected: {sid}")
        if sid in self.session_extension_to_agent:
            self.session_extension_to_agent[sid] = {
                key: value for key, value in self.session_extension_to_agent.items() if key[0] != sid
            }

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

    @validate_event(ExtensionCallBack)
    async def on_handle_chat_interrupt(self, sid, data: ExtensionCallBack):
        if not self._check_exist_agent(sid, data.extension_name):
            logger.error(f"Agent not found")
            await self.emit("error", "Agent not found", to=sid)
            return

        agent = self.session_extension_to_agent[(sid, data.extension_name)]

        action = HumanAction.CONTINUE if data.input.strip().lower() == "continue" else HumanAction.REFUSE
        result = await agent.async_handle_chat_interrupt(
            action=action,
            thread_id=data.thread_id,
            max_recursion=data.max_recursion if data.max_recursion is not None else 5,
        )

        if action == HumanAction.CONTINUE:
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

    @validate_event(ExtensionRequest)
    async def on_chat(self, sid, data: ExtensionRequest):
        try:
            if not self._check_exist_agent(sid, data.extension_name):
                agent = self._create_agent(data.extension_name, data.user_id)
                self.session_extension_to_agent[(sid, data.extension_name)] = agent

            agent = self.session_extension_to_agent[(sid, data.extension_name)]

            response = await agent.async_chat(
                question=data.input,
                thread_id=data.thread_id,
                max_recursion=data.max_recursion if data.max_recursion is not None else 5,
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

    @validate_event(ExtensionCallBack)
    async def _handle_stream_interrupt(self, sid, data: ExtensionCallBack):
        if not self._check_exist_agent(sid, data.extension_name):
            logger.error(f"Agent not found")
            await self.emit("error", "Agent not found", to=sid)
            return

        agent = self.session_extension_to_agent[(sid, data.extension_name)]

        action = HumanAction.CONTINUE if data.input.strip().lower() == "continue" else HumanAction.REFUSE
        result = await agent.async_handle_stream_interrupt(
            action=action,
            thread_id=data.thread_id,
            max_recursion=data.max_recursion if data.max_recursion is not None else 5,
        )

        async for dict_message in to_sse(result):
            message = convert_dict_message_to_message(dict_message)
            await self.emit(
                event="stream_response",
                data=ExtensionResponse(
                    user_id=data.user_id,
                    thread_id=data.thread_id,
                    extension_name=data.extension_name,
                    interrupted=False,
                    output=message
                ).model_dump(),
                to=sid
            )

    @validate_event(ExtensionRequest)
    async def on_stream(self, sid, data):
        try:
            if not self._check_exist_agent(sid, data.extension_name):
                agent = self._create_agent(data.extension_name, data.user_id)
                self.session_extension_to_agent[(sid, data.extension_name)] = agent

            agent = self.session_extension_to_agent[(sid, data.extension_name)]

            response = await agent.async_stream(
                question=data.input,
                thread_id=data.thread_id,
                max_recursion=data.max_recursion if data.max_recursion is not None else 5,
            )

            interrupted = False
            async for dict_message in to_sse(response):
                binary_score = convert_dict_message_to_binary_score(dict_message)
                if binary_score is not None:
                    interrupted = binary_score.interrupted
                else:
                    if interrupted:
                        tool_call = convert_dict_message_to_tool_call(dict_message)
                        if tool_call is not None:
                            await self.emit(
                                event="stream_response",
                                data=ExtensionResponse(
                                    user_id=data.user_id,
                                    thread_id=data.thread_id,
                                    extension_name=data.extension_name,
                                    interrupted=interrupted,
                                    output=tool_call
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
                                    interrupted=interrupted,
                                    output=message
                                ).model_dump(),
                                to=sid
                            )
        except Exception as e:
            logger.error(f"Error executing Gmail API: {str(e)}", exc_info=True)
            await self.emit("error", "Internal server error", to=sid)
