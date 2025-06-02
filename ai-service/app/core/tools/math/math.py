# This is an example showing how to create a simple calculator skill

import numexpr as ne
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field


class MathInput(BaseModel):
    expression: str = Field(description="Math Expression")


def math_calc(expression: str) -> str:
    try:
        result = ne.evaluate(expression)
        return str(result)
    except Exception:
        return f"Error evaluating expression: {expression}"


math = StructuredTool.from_function(
    func=math_calc,
    name="Math Calculator",
    description=" A tool for evaluating an math expression, calculated locally with NumExpr.",
    args_schema=MathInput,
    return_direct=False,
)
