import logging

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from app.core import settings

logger = logging.getLogger(__name__)


def get_embedding_model() -> Embeddings:
    try:
        api_key = settings.env_settings.OPENAI_API_KEY
        embedding_model = OpenAIEmbeddings(api_key=SecretStr(api_key))
        logger.info(f"Embedding model created: {type(embedding_model)}")

        # Check if the embedding model has a dimension attribute before logging it
        dimensions = getattr(embedding_model, "dimensions", None)
        if dimensions is not None:
            logger.info(f"Embedding model dimensions: {dimensions}")

        return embedding_model

    except Exception as e:
        logger.error(f"Error initializing embedding model: {e}", exc_info=True)
        raise
