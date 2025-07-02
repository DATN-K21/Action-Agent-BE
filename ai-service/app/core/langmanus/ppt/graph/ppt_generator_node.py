# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import os
import shutil
import subprocess

from app.core.langmanus.ppt.graph.state import PPTState

logger = logging.getLogger(__name__)


def _get_marp_command():
    """Get the appropriate Marp command for the current platform."""
    # Try different Marp command variations
    import shutil

    marp_path = shutil.which("marp.cmd")
    marp_commands = [marp_path, "marp", "npx @marp-team/marp-cli", "npx marp-cli"]

    for cmd in marp_commands:
        try:
            # Test if the command exists
            result = subprocess.run(cmd.split() + ["--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Using Marp command: {cmd}")
                return cmd.split()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    # Default fallback
    logger.warning("No Marp installation found, using default 'marp' command")
    return ["marp"]


def ppt_generator_node(state: PPTState):
    logger.info("Generating PPT file from markdown...")

    try:
        # Get session information
        session_id = state.get("session_id", "unknown_session")
        temp_dir = state.get("session_temp_dir")

        if not temp_dir or not os.path.exists(temp_dir):
            logger.error("Session temporary directory not found")
            raise RuntimeError("Session temporary directory not found")

        # Generate output PPT file path in the same temp directory
        generated_file_path = os.path.join(temp_dir, f"{session_id}.pptx")

        # Get cross-platform Marp command
        marp_cmd = _get_marp_command()

        # Build the full command
        cmd = marp_cmd + [
            state["ppt_file_path"],
            "-o",
            generated_file_path,
            "--theme",
            "default",  # Use default theme for better compatibility
            "--allow-local-files",  # Allow local file access if needed
        ]

        logger.info(f"Executing Marp command: {' '.join(cmd)}")

        # Execute Marp CLI command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            cwd=temp_dir,  # Set working directory to temp dir
        )

        if result.returncode != 0:
            logger.error(f"Marp command failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError(f"Failed to generate PPT: {result.stderr}")

        # Verify the output file was created
        if not os.path.exists(generated_file_path):
            logger.error(f"PPT file was not created at: {generated_file_path}")
            raise RuntimeError("PPT file generation failed")

        file_size = os.path.getsize(generated_file_path)
        logger.info(f"PPT file generated successfully: {generated_file_path} (Size: {file_size} bytes)")

        return {"generated_file_path": generated_file_path}

    except subprocess.TimeoutExpired:
        logger.error("Marp command timed out")
        raise RuntimeError("PPT generation timed out")
    except Exception as e:
        logger.error(f"Error during PPT generation: {str(e)}")
        raise RuntimeError(f"PPT generation failed: {str(e)}")


def cleanup_ppt_session(session_temp_dir: str):
    """Clean up the temporary session directory and all its contents."""
    try:
        if session_temp_dir and os.path.exists(session_temp_dir):
            shutil.rmtree(session_temp_dir)
            logger.info(f"Cleaned up temporary session directory: {session_temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary directory {session_temp_dir}: {str(e)}")
