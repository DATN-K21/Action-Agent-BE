import logging
import datetime
from typing import AsyncIterator

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from langchain_google_community.gmail.utils import (
    build_resource_service,
)
from langchain_google_community import GmailToolkit
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from app.services.models_service import get_openai_model
from app.memory.checkpoint import AsyncPostgresCheckpoint
from app.utils.stream import to_sse, astream_state

logger = logging.getLogger(__name__)

class GmailService:
    _CHECKPOINTER = AsyncPostgresCheckpoint.get_instance()
    _CLIENT_SECRETS_FILE = "private/auth/client_secrets.json"
    _SCOPES = ['https://mail.google.com/']
    _REDIRECT_URI = 'https://localhost:5001/gmail/auth/callback'

    # Fixed data for Gmail API
    _data = {
        'token': 'ya29.a0AeDClZDyDWWdRni416TU6Oc6x5y6vkIiJFYnMbIU5ZEEY1hAtKebQM_MPNRZ__SEmuYUroCfO5ZPUaHiezwyJAw7hiwH1fXQDUyc07BMt6l-kwGBxoE1xzUfKEl4C2uVgoZ3vK_Ph-AzBhFS4oVcm6A0VL-oGgk7IqkTA51IaCgYKAUoSARISFQHGX2Mi5-Ov2QtQ4P0awKtceue-9Q0175',
        'refresh_token': '1//0eMDKkCl13R4MCgYIARAAGA4SNwF-L9Ir_dUpns2awpX-Okm-yabfFJaPvTU5xUwFkri-7yzzxWm7CmucHRuuYz9NX_Zuy21C5W0',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': '817123526014-99uftd7rog2lcov76q1s1s2phtmtpig6.apps.googleusercontent.com',
        'client_secret': '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',
        'scopes': [
            'https://mail.google.com/'
        ],
        'universe_domain': 'googleapis.com',
        'account': '',
        'expiry': datetime.datetime(2024, 12, 8, 17, 26, 40, 778367)
    }
    # _data =  {
    #     "token": "ya29.a0AeDClZCaFKVkv73UxmKW3ZjxDSEEAAMN1OLHiolU88msgxrC4s3_KMPcj5HOOQtmOid2wbQTMomCcJn4Uc4rpMj6RAqcmVVjMTAIqQywKHpDM7JmXSYXcjErGEVLZuRY38_p9La0H8hGI6-J1fm0nqYWAX4xb4zQmKTjZKWVaCgYKASoSARESFQHGX2Mi55TaKbEGULlIUj_oSw66vQ0175",
    #     "refresh_token": "1//0gkm5G8VwjkXuCgYIARAAGBASNwF-L9IryGI1KsfHZvCKgSNWnciJDqd95CA9-YTIJfyKpTDlnQQ0ax8YbbONdqVfwxKh5rV5bys",
    #     "token_uri": "https://oauth2.googleapis.com/token",
    #     "client_id": "981366723685-sl8j0cbepu88qm3dt62sn50ndpikh75p.apps.googleusercontent.com",
    #     "client_secret": "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",
    #     "scopes": [
    #       "https://mail.google.com"
    #     ],
    #     "universe_domain": "googleapis.com",
    #     "account": "",
    #     "expiry": datetime.datetime(2024, 12, 10, 1, 12, 38, 835000)
    # }

    # Define OAuth flow object
    @classmethod
    def get_flow(cls):
        flow = Flow.from_client_secrets_file(
            cls._CLIENT_SECRETS_FILE,
            scopes=cls._SCOPES,
            redirect_uri=cls._REDIRECT_URI
        )
        return flow

    @classmethod
    def credentials_to_dict(cls, credentials):
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'universe_domain': credentials.universe_domain,
            'account': credentials.account,
            'expiry': credentials.expiry,
        }

    @classmethod
    def get_gmail_tools(cls, credentials=None):
        api_resource = build_resource_service(credentials=credentials)
        toolkit = GmailToolkit(api_resource=api_resource)
        return toolkit.get_tools()

    @classmethod
    def get_supported_actions(cls):
        actions = {
            "GmailCreateDraft": "Create a draft email. "
                                "Use this tool to create a draft email with the provided message fields.",
            "GmailSendMessage": "Send an email message. "
                                "Use this tool to send email messages. "
                                "The input is the message, recipients",
            "GmailSearch": "Search for emails. "
                           "Use this tool to search for email messages or threads. "
                           "The input must be a valid Gmail query. The output is a JSON list of the requested resource.",
            "GmailGetMessage": "Retrieve details of a specific email. "
                               "Use this tool to fetch an email by message ID. "
                               "Returns the thread ID, snippet, body, subject, and sender.",
            "GmailGetThread": "Retrieve the full thread of an email conversation. "
                              "Use this tool to search for email messages. "
                              "The input must be a valid Gmail query. "
                              "The output is a JSON list of messages."
        }
        return actions

    @classmethod
    def build_gmail_graph(cls, user_id: str):
        # Todo: use user_id to get respective credentials
        model = get_openai_model()
        credentials = Credentials(**cls._data)
        tools = cls.get_gmail_tools(credentials=credentials)

        graph = create_react_agent(model=model,
                                            tools=tools,
                                            checkpointer=cls._CHECKPOINTER)

        return graph

    @classmethod
    async def execute_gmail_debug(cls, user_id: str, thread_id: str, user_input: str, max_recursion: int = 5):
        try:
            graph = cls.build_gmail_graph(user_id)
            query = HumanMessage(user_input)
            config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}

            events = graph.astream(
                {"messages": [query]},
                config=config,
                stream_mode="values",
            )
            async for event in events:
                event["messages"][-1].pretty_print()

            return "Done"
        except Exception as e:
            logger.error(f"Error in execute gmail: {str(e)}")
            raise

    @classmethod
    async def get_gmail_history_debug(cls, user_id: str, thread_id: str, max_recursion: int = 5):
        try:
            graph = cls.build_gmail_graph(user_id)
            config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}
            history = graph.aget_state_history(config=config)

            async for message in history:
                print(message.values, message.next)

            return "Done"
        except Exception as e:
            logger.error(f"Error in get gmail history: {str(e)}")
            raise

    @classmethod
    async def execute_gmail(cls, user_id: str, thread_id: str, user_input: str, max_recursion: int = 5):
        try:
            graph = cls.build_gmail_graph(user_id)
            query = HumanMessage(user_input)
            config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}

            response = await graph.ainvoke(
                {"messages": [query]},
                config=config,
            )

            return response["messages"][-1].content
        except Exception as e:
            logger.error(f"Error in execute gmail: {str(e)}")
            raise

    @classmethod
    async def get_gmail_history(cls, user_id: str, thread_id: str, max_recursion: int = 5):
        try:
            graph = cls.build_gmail_graph(user_id)
            config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}
            history = graph.aget_state_history(config=config)

            return [
                {
                    "values": c.values,
                    "next": c.next,
                    "config": c.config,
                    "parent": c.parent_config,
                }
                async for c in history
            ]
        except Exception as e:
            logger.error(f"Error in get gmail history: {str(e)}")
            raise

    @classmethod
    def stream_gmail(
            cls,
            user_id: str,
            thread_id: str,
            user_input: str,
            max_recursion: int = 5) -> AsyncIterator[dict]:
        try:
            graph = cls.build_gmail_graph(user_id)
            config = {"recursion_limit": max_recursion, "configurable": {"thread_id": thread_id}}
            query = HumanMessage(user_input)

            return to_sse(astream_state(graph, input={"messages": [query]}, config=config))
        except Exception as e:
            logger.error(f"Error in stream gmail: {str(e)}")
            raise