import base64
import json
import queue
import threading
import time
import uuid
from textwrap import dedent

import docker
from docker.errors import ImageNotFound, NotFound
from docker.models.containers import Container
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from app.core import logging

from ....state import (
    ReturnWorkflowTeamState,
    WorkflowTeamState,
    parse_variables,
    update_node_outputs,
)

logger = logging.get_logger(__name__)


class ContainerPool:
    """Manages a pool of Docker containers"""

    def __init__(self, image_tag: str, pool_size: int = 3, memory_limit: str = "256m"):
        self.image_tag = image_tag
        self.pool_size = pool_size
        self.memory_limit = memory_limit
        self.available_containers = queue.Queue()
        self.active_containers = {}  # Use dictionary to track containers
        self.client = docker.from_env()
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize container pool"""
        container = self._create_container()
        self.available_containers.put(container)

    def _create_container(self):
        """Create a new container"""
        container_name = f"code-interpreter-worker-{len(self.active_containers)}"
        try:
            logger.info(f"Creating container: {container_name}")
            # First try to delete a container with the same name
            try:
                old_container = self.client.containers.get(container_name)
                old_container.remove(force=True)
                logger.info(f"Removed old container: {container_name}")
            except NotFound:
                pass

            # Create a new container
            # noinspection PyTypeChecker
            container = self.client.containers.run(
                self.image_tag,
                detach=True,
                tty=True,
                working_dir="/workspace",
                remove=True,  # Automatically delete when the container stops
                stdin_open=True,
                network="docker_default",
                volumes={"app-code-workspace": {"bind": "/workspace", "mode": "rw"}},
                mem_limit=self.memory_limit,
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
                name=container_name,
                command=[
                    "/bin/bash",
                    "/opt/code-interpreter/scripts/entrypoint.sh",
                ],  # Explicitly specify the startup command
            )

            # Wait for the container to fully start
            time.sleep(0.5)
            container.reload()

            self.active_containers[container.id] = container
            logger.info(f"Created container: {container_name}")
            return container

        except Exception as e:
            logger.error(f"Error creating container: {e}")
            raise

    def get_container(self):
        """Get an available container"""
        with self.lock:
            try:
                container = self.available_containers.get_nowait()
                # Check if container is still running
                try:
                    container.reload()
                    return container
                except Exception:
                    # Use pop instead of discard because it's a dictionary
                    self.active_containers.pop(container.id, None)
                    return self._create_container()
            except queue.Empty:
                if len(self.active_containers) < self.pool_size:
                    return self._create_container()
                else:
                    # Wait for an available container
                    return self.available_containers.get(timeout=5)

    def return_container(self, container):
        """Return container to the pool"""
        with self.lock:
            try:
                container.reload()  # Check container status
                container.exec_run("rm -rf /workspace/*")  # Clean the workspace directory
                self.available_containers.put(container)
            except Exception:
                # Use pop instead of discard since it's a dictionary
                self.active_containers.pop(container.id, None)
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def cleanup(self):
        """Clean up all containers"""
        with self.lock:
            # Clean up active containers
            for container_id, container in list(self.active_containers.items()):
                try:
                    logger.info(f"Removing container: {container.name}")
                    container.remove(force=True)
                except Exception as e:
                    logger.error(f"Error removing container: {e}")
                finally:
                    self.active_containers.pop(container_id, None)

            # Clean up all code-interpreter-worker containers
            try:
                containers = self.client.containers.list(
                    all=True, filters={"name": "code-interpreter-worker"}
                )
                for container in containers:
                    try:
                        container.remove(force=True)
                        logger.info(f"Removed worker container: {container.name}")
                    except Exception as e:
                        logger.error(f"Error removing worker container: {e}")
            except Exception as e:
                logger.error(f"Error listing containers: {e}")

    def __del__(self):
        """Ensure all containers are cleaned up when the object is destroyed"""
        self.cleanup()


class CodeTemplate:
    """Code Template Management Class"""

    _code_placeholder = "{code}"
    _inputs_placeholder = "{inputs}"

    @classmethod
    def get_runner_script(cls) -> str:
        """Create standardized execution script template"""
        runner_script = dedent(
            f"""
            # User defined function
            {cls._code_placeholder}

            import json, ast

            def find_function_name(code):
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        return node.name
                return None

            # Analyze code to get function name
            code = '''{cls._code_placeholder}'''
            function_name = find_function_name(code)

            if not function_name:
                raise Exception("No function found in the code")

            # Execute code
            exec(code)

            # Execute function and get result
            result = eval(f"{{function_name}}()")

            # Convert result to JSON and logger.info
            output_json = json.dumps(result, indent=4)
            logger.info(f'<<RESULT>>{{output_json}}<<RESULT>>')
            """
        )
        return runner_script

    @classmethod
    def create_execution_script(cls, code: str, inputs: dict | None = None) -> str:
        """Create complete execution script"""
        runner_script = cls.get_runner_script()
        # Replace placeholders
        script = runner_script.replace(cls._code_placeholder, code)
        if inputs:
            inputs_json = json.dumps(inputs)
            script = script.replace(cls._inputs_placeholder, inputs_json)
        return script


class CodeExecutor:
    """Code execution engine using Docker with container pooling"""

    _instance = None
    _pool = None

    # Python built-in libraries, no installation needed
    BUILTIN_LIBRARIES = {
        "os",
        "sys",
        "glob",
        "json",
        "time",
        "datetime",
        "random",
        "math",
        "re",
        "collections",
        "itertools",
        "functools",
        "pathlib",
        "base64",
        "hashlib",
        "uuid",
        # ... other built-in libraries
    }

    # Pre-installed third-party libraries
    PREINSTALLED_LIBRARIES = {
        "numpy",
        "pandas",
        "requests",
        "python-dateutil",
        "matplotlib",
        # ... other pre-installed third-party libraries
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CodeExecutor, cls).__new__(cls)
        return cls._instance

    def __init__(
            self,
            timeout: int = 30,
            memory_limit: str = "256m",
            image_tag: str = "flock-code-interpreter:latest",
            pool_size: int = 3,
    ):
        if not hasattr(self, "initialized"):
            self.timeout = timeout
            self.memory_limit = memory_limit
            self.image_tag = image_tag
            self.client = docker.from_env()
            self._verify_docker_image()
            self._pool = ContainerPool(
                image_tag=image_tag, pool_size=pool_size, memory_limit=memory_limit
            )
            self.initialized = True

        # Ensure pool is always initialized
        elif self._pool is None:
            self._pool = ContainerPool(image_tag=self.image_tag, pool_size=pool_size, memory_limit=self.memory_limit)

    def _verify_docker_image(self) -> None:
        """Verify if Docker image exists, build if not"""
        try:
            self.client.images.get(self.image_tag)
        except ImageNotFound:
            # Update Dockerfile path
            dockerfile_path = "./docker/code-interpreter"
            self.client.images.build(path=dockerfile_path, tag=self.image_tag, rm=True)

    def _install_libraries(self, container: Container, libraries: list[str]) -> None:
        """Install required libraries in container"""
        # Filter out built-in libraries and pre-installed libraries
        libraries_to_install = [
            lib
            for lib in libraries
            if lib.lower() not in self.PREINSTALLED_LIBRARIES
               and lib.lower() not in self.BUILTIN_LIBRARIES
        ]

        if libraries_to_install:
            logger.info(f"Installing libraries: {', '.join(libraries_to_install)}")
            for library in libraries_to_install:
                container.exec_run(f"pip install --user {library}")
        else:
            logger.info("All required libraries are pre-installed or built-in")

    def execute(self, code: str, libraries: list[str]) -> str:
        """Execute code in Docker container with safety measures"""
        logger.info(f"\nStarting code execution with {len(libraries)} libraries")
        if libraries:
            logger.info(f"Required libraries: {', '.join(libraries)}")

        if self._pool is None:
            error_msg = "Container pool is not initialized"
            return error_msg

        container = self._pool.get_container()
        logger.info(f"Using container: {container.name}")

        try:
            # Install required libraries
            self._install_libraries(container, libraries)
            logger.info("Libraries installed successfully")

            # Create execution script using a template
            runner_script = CodeTemplate.create_execution_script(code)

            # Encoding needed only once
            code_base64 = base64.b64encode(runner_script.encode("utf-8")).decode(
                "utf-8"
            )
            decode_and_exec = f'''python3 -c "import base64; exec(base64.b64decode('{code_base64}').decode('utf-8'))"'''

            # Execute code
            exec_result = container.exec_run(
                decode_and_exec, tty=True, environment={"PYTHONUNBUFFERED": "1"}
            )

            if exec_result.exit_code != 0:
                error_msg = (
                    f"Error executing code: {exec_result.output.decode('utf-8')}"
                )
                logger.info(f"\nError: {error_msg}")
                return error_msg

            result = exec_result.output.decode("utf-8")

            # Parse the results from the output
            import re

            result_match = re.search(r"<<RESULT>>(.+?)<<RESULT>>", result, re.DOTALL)
            if result_match:
                result_json = result_match.group(1)
                try:
                    result = json.loads(result_json.strip())
                    return result
                except json.JSONDecodeError as e:
                    logger.info(f"JSON decode error: {e}")
                    return result_json.strip()

            logger.info("\nCode execution result:")
            logger.info(result)
            return result

        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            logger.info(f"\nError: {error_msg}")
            return error_msg

        finally:
            logger.info("Returning container to pool")
            self._pool.return_container(container)

    def cleanup(self):
        """Clean up all resources"""
        if self._pool:
            self._pool.cleanup()

    def __del__(self):
        """Ensure resources are cleaned up when the object is destroyed"""
        self.cleanup()


class CodeNode:
    """Node for executing Python code in workflow"""

    def __init__(
            self,
            node_id: str,
            code: str,
            libraries: list[str] | None = None,
            timeout: int = 30,
            memory_limit: str = "256m",
    ):
        self.node_id = node_id
        self.code = code
        self.libraries = libraries or []
        self.executor = CodeExecutor(timeout=timeout, memory_limit=memory_limit)

    async def work(
            self, state: WorkflowTeamState, config: RunnableConfig
    ) -> ReturnWorkflowTeamState:
        """Execute code and update state"""
        if "node_outputs" not in state:
            state["node_outputs"] = {}

        try:
            # Parse variables in code
            parsed_code = parse_variables(
                self.code, state["node_outputs"], is_code=True
            )

            # Execute code
            code_execution_result = self.executor.execute(parsed_code, self.libraries)

            if isinstance(code_execution_result, str):
                # If code_result is a string, return it as it is
                code_result = code_execution_result
            elif isinstance(code_execution_result, dict):
                if "res" in code_execution_result:
                    # If the dictionary contains the "result" key, return its value
                    code_result = code_execution_result["res"]
                else:
                    code_result = "Error: The Code Execution Result must return a dictionary with the 'res' key."
            else:
                code_result = "Error: Invalid code return type, please return a dictionary with the 'res' key."

            result = ToolMessage(
                content=code_result,
                name="CodeExecutor",
                tool_call_id=str(uuid.uuid4()),
            )

            # Update node outputs
            new_output = {self.node_id: {"response": result.content}}
            state["node_outputs"] = update_node_outputs(
                state["node_outputs"], new_output
            )

            return_state: ReturnWorkflowTeamState = {
                "history": state.get("history", []) + [result],
                "messages": [result],
                "all_messages": state.get("all_messages", []) + [result],
                "node_outputs": state["node_outputs"],
            }
            return return_state

        except Exception as e:
            error_message = f"Code execution failed: {str(e)}"

            result = ToolMessage(
                content=error_message,
                name="CodeExecutor",
                tool_call_id=str(uuid.uuid4()),
            )

            new_output = {self.node_id: {"response": result.content}}
            state["node_outputs"] = update_node_outputs(
                state["node_outputs"], new_output
            )
            return_state: ReturnWorkflowTeamState = {
                "history": state.get("history", []) + [result],
                "messages": [result],
                "all_messages": state.get("all_messages", []) + [result],
                "node_outputs": state["node_outputs"],
            }
            return return_state
