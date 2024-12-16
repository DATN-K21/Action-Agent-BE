from langchain_openai import ChatOpenAI

MAX_TOKENS = 10000

def get_openai_model(model: str = "gpt-4o", temperature= 0, streaming = True):
    """Get an OpenAI language model."""
    return ChatOpenAI(temperature=temperature, streaming=streaming, model_name=model)
