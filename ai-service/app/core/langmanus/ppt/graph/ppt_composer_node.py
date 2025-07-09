# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
import tempfile
import uuid

from langchain.schema import HumanMessage, SystemMessage

from app.core import logging
from app.core.langmanus.config.agents import AGENT_LLM_MAP
from app.core.langmanus.llms.llm import get_llm_by_type
from app.core.langmanus.prompts.template import get_prompt_template

from .state import PPTState

logger = logging.get_logger(__name__)


def ppt_composer_node(state: PPTState):
    logger.info("Generating PPT content...")
    model = get_llm_by_type(AGENT_LLM_MAP["ppt_composer"])
    ppt_content = model.invoke(
        [
            SystemMessage(content=get_prompt_template("ppt/ppt_composer")),
            HumanMessage(content=state["input"]),
        ],
    )
    logger.info("PPT content generated successfully")

    # Generate unique session ID for this PPT generation request
    session_id = f"ppt_session_{uuid.uuid4()}"

    # Create temporary directory for this session
    temp_dir = tempfile.mkdtemp(prefix=session_id + "_")
    temp_ppt_file_path = os.path.join(temp_dir, f"{session_id}.md")

    # Write PPT content to temporary markdown file
    with open(temp_ppt_file_path, "w", encoding="utf-8") as f:
        f.write(ppt_content.content)  # type: ignore

    logger.info(f"PPT markdown saved to: {temp_ppt_file_path}")
    return {"ppt_content": ppt_content, "ppt_file_path": temp_ppt_file_path, "session_temp_dir": temp_dir, "session_id": session_id}
