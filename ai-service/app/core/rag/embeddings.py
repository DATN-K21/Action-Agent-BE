import json
import logging

import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.model_providers.model_provider_manager import model_provider_manager
from app.core.settings import env_settings
from app.core.workflow.utils.db_utils import db_operation
from app.db_models import Model, ModelProvider

logger = logging.getLogger(__name__)


def get_api_key(provider_name: str) -> str:
    def _get_api_key(session: Session):
        provider = session.execute(select(ModelProvider).where(ModelProvider.provider_name == provider_name)).first()
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")
        return provider.decrypted_api_key

    return db_operation(_get_api_key)


def get_embedding_dimension(provider_name: str, model_name: str) -> int:
    def _get_dimension(session: Session):
        provider = session.execute(select(ModelProvider).where(ModelProvider.provider_name == provider_name)).first()
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")

        model = session.execute(select(Model).where(Model.ai_model_name == model_name)).first()

        if not model:
            # If not found in the database, get from configuration
            provider_models = model_provider_manager.get_supported_models(provider_name)
            model_info = next(
                (m for m in provider_models if m["name"] == model_name), None
            )
            if not model_info or "dimension" not in model_info:
                raise ValueError(
                    f"No dimension information found for model {model_name}"
                )
            dimension = model_info["dimension"]
        else:
            dimension = model.metadata_.get("dimension")
            if dimension is None:
                raise ValueError(
                    f"No dimension information found in database for model {model_name}"
                )

        return dimension

    return db_operation(_get_dimension)


class ZhipuAIEmbeddings(BaseModel, Embeddings):
    api_key: str
    model: str = "embedding-3"
    dimension: int | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dimension = get_embedding_dimension("zhipuai", self.model)

    class Config:
        extra = "forbid"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=self.api_key)
        response = client.embeddings.create(model=self.model, input=texts)
        embeddings = [item.embedding for item in response.data]
        if embeddings:
            self.dimension = len(embeddings[0])
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class SiliconFlowEmbeddings(BaseModel, Embeddings):
    api_key: str
    model: str = "BAAI/bge-large-zh-v1.5"
    dimension: int | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dimension = get_embedding_dimension("siliconflow", self.model)

    class Config:
        extra = "forbid"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        url = "https://api.siliconflow.cn/v1/embeddings"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"model": self.model, "input": texts, "encoding_format": "float"}
        response = requests.post(url, json=payload, headers=headers)
        response_json = response.json()
        logger.debug(
            f"SiliconFlow API response: {json.dumps(response_json, indent=2)[:20]}"
        )

        if "data" not in response_json or not isinstance(response_json["data"], list):
            raise ValueError(
                f"Unexpected response format from SiliconFlow API: {response_json}"
            )

        embeddings = []
        for item in response_json["data"]:
            if "embedding" not in item or not isinstance(item["embedding"], list):
                raise ValueError(f"Unexpected embedding format in response: {item}")
            embeddings.append(item["embedding"])

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def get_embedding_model(model__provider_name: str) -> Embeddings:
    logger.info(f"Initializing embedding model: {model__provider_name}")
    try:
        if model__provider_name == "openai":
            api_key = get_api_key("openai")
            embedding_model = OpenAIEmbeddings(api_key=SecretStr(api_key))
            # Store dimension as a separate attribute since OpenAIEmbeddings doesn't have a dimension attribute
            dimension = get_embedding_dimension("openai", "text-embedding-ada-002")
            # Add dimension as a separate attribute to the embedding_model
            setattr(embedding_model, "dimension", dimension)
        elif model__provider_name == "zhipuai":
            api_key = get_api_key("zhipuai")
            embedding_model = ZhipuAIEmbeddings(api_key=api_key)
        elif model__provider_name == "siliconflow":
            api_key = get_api_key("siliconflow")
            embedding_model = SiliconFlowEmbeddings(api_key=api_key)
        elif model__provider_name == "local":
            embedding_model = HuggingFaceEmbeddings(
                model_name=env_settings.DENSE_EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
            )
            # For local models, we can get the dimension by actually embedding a sample text
            sample_embedding = embedding_model.embed_query("Sample text for dimension")
            setattr(embedding_model, "dimension", len(sample_embedding))
        else:
            raise ValueError(
                f"Unsupported embedding model provider: {model__provider_name}"
            )

        logger.info(f"Embedding model created: {type(embedding_model)}")

        # Check if the embedding model has a dimension attribute before logging it
        dimension = getattr(embedding_model, "dimension", None)
        if dimension is not None:
            logger.info(f"Embedding model dimension: {dimension}")

        return embedding_model
    except Exception as e:
        logger.error(f"Error initializing embedding model: {e}", exc_info=True)
        raise
