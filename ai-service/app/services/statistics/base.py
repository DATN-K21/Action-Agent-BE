from app.core.enums import StatisticsEntity
from app.db_models import (
    Assistant,
    ConnectedExtension,
    Thread,
    User,
)
from app.db_models.base_entity import BaseEntity


class BaseStatisticsService:
    """
    Base class for statistics services.
    This class should be extended by any specific statistics service implementation.
    """

    @staticmethod
    def get_entity_statistics_model(entity: StatisticsEntity) -> type[BaseEntity]:
        """
        Get the appropriate statistics database model based on the entity type.
        """
        if entity == StatisticsEntity.USERS:
            return User
        elif entity == StatisticsEntity.CONNECTED_EXTENSIONS:
            return ConnectedExtension
        elif entity == StatisticsEntity.THREADS:
            return Thread
        elif entity == StatisticsEntity.ASSISTANTS:
            return Assistant
        else:
            raise ValueError(f"Unsupported entity type: {entity}")
