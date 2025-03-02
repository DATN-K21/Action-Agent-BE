from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.memory.checkpoint import AsyncPostgresPool


async def get_checkpointer() -> AsyncPostgresSaver:
    """Get the checkpointer singleton."""
    return await AsyncPostgresPool.get_checkpointer()
