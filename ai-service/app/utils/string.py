import re


def to_snake_case(string: str) -> str:
    """Converts a string to snake_case."""
    return re.sub(r"([a-z])([A-Z])", r"\1_\2", string).lower()
