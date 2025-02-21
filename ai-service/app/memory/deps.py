from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.memory.checkpoint import AsyncPostgresCheckpoint


def get_checkpointer() -> AsyncPostgresSaver:
    """Get the checkpointer singleton."""
    return AsyncPostgresCheckpoint.get_instance()
