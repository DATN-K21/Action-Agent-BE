from typing import Callable, Sequence, Union

from langchain_core.tools import BaseTool

from app.core.graph.base import GraphBuilder


class ExtensionBuilderManager:
    def __init__(self):
        self.name_to_builder = {}


    def update_builder_tools(self, builder_name: str, tools: Sequence[Union[BaseTool, Callable]]):
        if builder_name not in self.name_to_builder:
            raise ValueError(f"Builder '{builder_name}' does not exist")

        self.name_to_builder[builder_name].tools = tools


    def register_extension_builder(self, builder: GraphBuilder):
        if builder.name is None:
            raise ValueError("Builder name must be provided")

        if builder.name in self.name_to_builder:
            raise ValueError(f"Builder '{builder.name}' already exists")

        self.name_to_builder[builder.name] = builder


    def remove_extension_builder(self, name: str):
        if name in self.name_to_builder:
            del self.name_to_builder[name]
            return


    def get_extension_builder(self, name: str) -> GraphBuilder | None:
        if name in self.name_to_builder:
            return self.name_to_builder[name]

        return None


    def get_all_extension_builders(self) -> Sequence[GraphBuilder]:
        return list(self.name_to_builder.values())


    def get_all_extension_builder_names(self) -> Sequence[str]:
        return list(self.name_to_builder.keys())