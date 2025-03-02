from typing import Sequence

from langchain_community.retrievers import WikipediaRetriever
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.runnables import ConfigurableField
from langchain_core.tools import BaseTool, create_retriever_tool
from pydantic import SecretStr

from app.core.settings import env_settings
from app.utils.uploading import vstore


def get_search_tools(max_results: int = 5) -> Sequence[BaseTool]:
    api_wrapper = TavilySearchAPIWrapper(tavily_api_key=SecretStr(env_settings.TAVILY_API_KEY))
    tavily_tool = TavilySearchResults(
        max_results=max_results,
        name="tavily_search_tool",
        api_wrapper=api_wrapper,
        description="Search and return information from Tavily",
    )

    wikipedia_retriever = WikipediaRetriever(wiki_client=None)
    wikipedia_retriever_tool = create_retriever_tool(
        wikipedia_retriever,
        "wikipedia_retriever_tool",
        "Search and return information from Wikipedia",
    )
    return [tavily_tool, wikipedia_retriever_tool]


def get_rag_tools() -> Sequence[BaseTool]:
    retriever = vstore.as_retriever()
    configurable_retriever = retriever.configurable_fields(
        search_kwargs=ConfigurableField(
            id="search_kwargs",
            name="Search Kwargs",
            description="The search kwargs to use",
        )
    )

    retrieve_tool = create_retriever_tool(
        configurable_retriever,  # type: ignore
        "retriever_tool",
        "Search and return information from the most relevant documents",
    )

    return [retrieve_tool]
