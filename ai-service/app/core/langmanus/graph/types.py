# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from typing import Optional

from langgraph.graph import MessagesState

from app.core.langmanus.prompts.planner_model import Plan
from app.core.langmanus.rag import Resource


class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    locale: str
    observations: list[str]
    resources: list[Resource]
    plan_iterations: int
    current_plan: Optional[Plan | str]
    final_report: str
    auto_accepted_plan: bool
    enable_background_investigation: bool
    background_investigation_results: Optional[str]
