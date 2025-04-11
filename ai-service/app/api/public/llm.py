from fastapi import APIRouter, Depends

from app.api.auth import ensure_authenticated
from app.core import logging
from app.prompts.prompt_templates import get_title_generation_prompt_template
from app.schemas.agent import AgentChatResponse
from app.schemas.base import ResponseWrapper
from app.schemas.llm import GenerateTitleRequest, GenerateTitleResponse
from app.services.model_service import get_chat_model

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/generate-title", summary="Generate title from the content.",
             response_model=ResponseWrapper[AgentChatResponse])
async def generate_title(
        request: GenerateTitleRequest,
        _: bool = Depends(ensure_authenticated),
):
    try:
        model = get_chat_model()
        prompt = get_title_generation_prompt_template()
        chain = prompt | model
        title = await chain.ainvoke({"content": request.content})
        return ResponseWrapper.wrap(status=200, data=GenerateTitleResponse(title=title.content)).to_response()

    except Exception as e:
        logger.error(f"Error fetching llm: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
