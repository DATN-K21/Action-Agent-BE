import re


def standardize_string(s: str) -> str:
    """
    Beautifies and standardizes a string to match the pattern: ^[^\s<|\\/>]+$
    - Converts to snake_case (Python format name).
    - Removes whitespace and the characters: < | \ / >
    - Returns the cleaned string.
    """
    # Convert to snake_case: lowercase, replace spaces and hyphens with underscores
    s = re.sub(r"[\s\-]+", "_", s.strip().lower())
    # Remove forbidden characters
    s = re.sub(r"[<|\\/>]", "", s)
    # Remove any remaining whitespace (shouldn't be any after above)
    s = re.sub(r"\s", "", s)
    return s
