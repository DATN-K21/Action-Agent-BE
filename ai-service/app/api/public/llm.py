from fastapi import APIRouter, Depends

from app.api.auth import ensure_authenticated
from app.core import logging
from app.prompts.prompt_templates import get_title_generation_prompt_template
from app.schemas.agent import AgentChatResponse
from app.schemas.base import ResponseWrapper
from app.schemas.llm import GenerateTitleRequest, GenerateTitleResponse
from app.services.model_service import get_openai_model

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/generate-title", summary="Generate title from the content.", response_model=ResponseWrapper[AgentChatResponse])
async def generate_title(
    request: GenerateTitleRequest,
    _: bool = Depends(ensure_authenticated),
):
    try:
        model = get_openai_model()
        prompt = get_title_generation_prompt_template()
        chain = prompt | model
        title = await chain.ainvoke({"content": request.content})
        if isinstance(title.content, str):
            generated_title = title.content
        else:
            generated_title = "General topic"

        return ResponseWrapper.wrap(status=200, data=GenerateTitleResponse(title=generated_title)).to_response()

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
