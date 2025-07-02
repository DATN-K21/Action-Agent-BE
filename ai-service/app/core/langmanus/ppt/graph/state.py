# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT


from langgraph.graph import MessagesState


class PPTState(MessagesState):
    """State for the PPT generation."""

    # Input
    input: str

    # Output
    generated_file_path: str

    # Assets
    ppt_content: str
    ppt_file_path: str

    # Session management
    session_temp_dir: str
    session_id: str
