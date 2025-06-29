from typing import Any, List, Optional, Tuple

from sqlalchemy import case, func, select

from app.api.deps import SessionDep
from app.core.enums import DateRangeEnum, StatisticsEntity
from app.core.utils.date_range import get_period_range
from app.db_models.assistant import Assistant
from app.db_models.base_entity import BaseEntity
from app.db_models.connected_extension import ConnectedExtension
from app.db_models.skill import Skill
from app.db_models.thread import Thread
from app.db_models.upload import Upload
from app.db_models.user import User
from app.schemas.statistics import RankingStatisticsResponse
from app.services.statistics.base import BaseStatisticsService


class RankingStatisticsService(BaseStatisticsService):
    """
    Service for handling ranking statistics with composite activity scoring.
    """

    RANKING_LIMIT = 10  # Limit for the number of top entities to return
    # Activity scoring weights (industry best practices for user engagement)
    USER_ACTIVITY_WEIGHTS = {
        "uploads": 3.0,  # File uploads show high engagement
        "threads": 2.0,  # Starting conversations is valuable
        "assistants": 4.0,  # Creating assistants shows advanced usage
        "writes": 1.0,  # Messages/interactions are numerous but lower weight
    }
    EXTENSION_ACTIVITY_WEIGHTS = {
        "skills": 5.0,  # Skills show extension utility
        "connection_status": 10.0,  # Successful connections are critical
    }

    @staticmethod
    async def get_ranking_statistics(
        entity: StatisticsEntity, session: SessionDep, period: DateRangeEnum
    ) -> Tuple[List[RankingStatisticsResponse], dict]:
        """
        Get ranking statistics for a specific entity and period.
        """
        if entity == StatisticsEntity.USERS:
            return await RankingStatisticsService._get_user_activity_ranking(session, period)
        elif entity == StatisticsEntity.CONNECTED_EXTENSIONS:
            return await RankingStatisticsService._get_connected_extension_ranking(session, period)
        else:
            # For other entities, return empty list
            return [], {}

    @staticmethod
    async def _create_activity_subquery(
        EntityModel: type[BaseEntity],
        column_name: str,
        count_label: str,
        period: DateRangeEnum,
        additional_filters: Optional[Any] = None,
    ):
        """
        Generic function to create activity count subqueries.

        Args:
            EntityModel: The SQLAlchemy model to query
            group_by_column: Column to group by (e.g., User.id, ConnectedExtension.id)
            count_label: Label for the count column
            period: Time period for filtering
            additional_filters: Additional WHERE conditions
        """
        start_date, end_date = get_period_range(period)

        # Build date filter condition
        date_filter = True
        if start_date and end_date and hasattr(EntityModel, "created_at"):
            date_filter = EntityModel.created_at.between(start_date, end_date)

        # Get the column to group by
        group_by_column = EntityModel.__table__.c[column_name] if isinstance(column_name, str) else column_name

        # Build the base query
        query = (
            select(group_by_column, func.count(EntityModel.id).label(count_label))
            .where(EntityModel.is_deleted.is_(False) & date_filter)
            .group_by(group_by_column)
        )

        # Add additional filters if provided
        if additional_filters is not None:
            query = query.where(additional_filters)

        return query.subquery()

    @staticmethod
    async def _build_ranking_query(
        EntityModel: type[BaseEntity],
        subqueries: List[Tuple[Any, str]],  # List of (subquery, join_column_name)
        score_calculation: Any,
        select_columns: List[Any],
        main_model_filter: Optional[Any] = None,
    ):
        """
        Generic function to build ranking queries with joins and scoring.

        Args:
            EntityModel: The main model to select from
            subqueries: List of tuples (subquery, join_column_name)
            score_calculation: SQLAlchemy expression for score calculation
            select_columns: Columns to select in the final query
            main_model_filter: Additional filter for the main model
        """
        query = select(*select_columns).select_from(EntityModel)

        # Add outer joins for each subquery
        for subquery, join_column in subqueries:
            main_id_column = getattr(EntityModel, "id")
            subquery_join_column = getattr(subquery.c, join_column)
            query = query.outerjoin(subquery, main_id_column == subquery_join_column)

        # Add filters
        base_filter = EntityModel.is_deleted.is_(False)
        if main_model_filter is not None:
            base_filter = base_filter & main_model_filter

        # Get all non-aggregate columns for GROUP BY
        group_by_columns = []
        for column in select_columns:
            if hasattr(column, "element") and hasattr(column.element, "table"):
                group_by_columns.append(column)
            elif hasattr(column, "table"):
                group_by_columns.append(column)

        query = (
            query.where(base_filter)
            .group_by(*group_by_columns)
            .having(score_calculation > 0)
            .order_by(score_calculation.desc())
            .limit(RankingStatisticsService.RANKING_LIMIT)
        )

        return query

    @staticmethod
    async def _get_user_activity_ranking(session: SessionDep, period: DateRangeEnum) -> Tuple[List[RankingStatisticsResponse], dict]:
        """
        Get top users ranked by composite activity score.

        Activity score calculation:
        - Uploads: 3 points each (high-value content creation)
        - Threads: 2 points each (conversation initiation)
        - Assistants: 4 points each (advanced feature usage)
        - Writes: 1 point each (message interactions) - Only if Write has created_at
        """
        # Create activity subqueries using the generic function
        uploads_subq = await RankingStatisticsService._create_activity_subquery(Upload, "user_id", "upload_count", period)
        threads_subq = await RankingStatisticsService._create_activity_subquery(Thread, "user_id", "thread_count", period)
        assistants_subq = await RankingStatisticsService._create_activity_subquery(Assistant, "user_id", "assistant_count", period)

        # Calculate composite activity score
        score_calculation = (
            func.coalesce(uploads_subq.c.upload_count, 0) * RankingStatisticsService.USER_ACTIVITY_WEIGHTS["uploads"]
            + func.coalesce(threads_subq.c.thread_count, 0) * RankingStatisticsService.USER_ACTIVITY_WEIGHTS["threads"]
            + func.coalesce(assistants_subq.c.assistant_count, 0) * RankingStatisticsService.USER_ACTIVITY_WEIGHTS["assistants"]
        )

        # Define select columns
        select_columns = [
            User.id,
            User.username,
            User.email,
            func.coalesce(uploads_subq.c.upload_count, 0).label("upload_count"),
            func.coalesce(threads_subq.c.thread_count, 0).label("thread_count"),
            func.coalesce(assistants_subq.c.assistant_count, 0).label("assistant_count"),
            score_calculation.label("activity_score"),
        ]

        # Build the main query using the generic function
        subqueries_info = [
            (uploads_subq, "user_id"),
            (threads_subq, "user_id"),
            (assistants_subq, "user_id"),
        ]

        query = await RankingStatisticsService._build_ranking_query(User, subqueries_info, score_calculation, select_columns)

        result = await session.execute(query)
        rows = result.fetchall()

        # Convert to response objects with ranking and detailed breakdown
        ranking_results = []
        for rank, row in enumerate(rows, 1):
            ranking_results.append(
                RankingStatisticsResponse(
                    id=row.id,
                    rank=rank,
                    score=float(row.activity_score),
                    display_info={
                        "username": row.username,
                        "email": row.email,
                        "upload_count": str(row.upload_count),
                        "thread_count": str(row.thread_count),
                        "assistant_count": str(row.assistant_count),
                    },
                )
            )

        score_weights = {
            "uploads": RankingStatisticsService.USER_ACTIVITY_WEIGHTS["uploads"],
            "threads": RankingStatisticsService.USER_ACTIVITY_WEIGHTS["threads"],
            "assistants": RankingStatisticsService.USER_ACTIVITY_WEIGHTS["assistants"],
        }
        return ranking_results, score_weights

    @staticmethod
    async def _get_connected_extension_ranking(session: SessionDep, period: DateRangeEnum) -> Tuple[List[RankingStatisticsResponse], dict]:
        """
        Get top connected extensions ranked by usage and skill count.

        Activity score calculation for extensions:
        - Number of skills created: 5 points each (shows extension utility)
        - Success rate: Up to 10 points (connection_status == SUCCESS)
        - Recency: Recent connections get bonus points
        """
        # Create skill count subquery using the generic function
        skills_subq = await RankingStatisticsService._create_activity_subquery(Skill, "extension_id", "skill_count", period)

        # Calculate composite activity score for extensions
        score_calculation = func.coalesce(skills_subq.c.skill_count, 0) * RankingStatisticsService.EXTENSION_ACTIVITY_WEIGHTS["skills"] + case(
            (ConnectedExtension.connection_status == "success", RankingStatisticsService.EXTENSION_ACTIVITY_WEIGHTS["connection_status"]), else_=0.0
        )

        # Define select columns
        select_columns = [
            ConnectedExtension.id,
            ConnectedExtension.extension_name,
            ConnectedExtension.connection_status,
            func.coalesce(skills_subq.c.skill_count, 0).label("skill_count"),
            score_calculation.label("activity_score"),
        ]

        # Build the main query using the generic function
        subqueries_info = [
            (skills_subq, "extension_id"),
        ]

        query = await RankingStatisticsService._build_ranking_query(ConnectedExtension, subqueries_info, score_calculation, select_columns)

        result = await session.execute(query)
        rows = result.fetchall()

        # Convert to response objects with ranking and detailed breakdown
        ranking_results = []
        for rank, row in enumerate(rows, 1):
            ranking_results.append(
                RankingStatisticsResponse(
                    id=row.id,
                    score=float(row.activity_score),
                    rank=rank,
                    display_info={
                        "extension_name": row.extension_name or f"Extension {row.id[:8]}",
                        "connection_status": row.connection_status,
                        "skill_count": str(row.skill_count),
                    },
                )
            )

        score_weights = {
            "skills": RankingStatisticsService.EXTENSION_ACTIVITY_WEIGHTS["skills"],
            "connection_status": RankingStatisticsService.EXTENSION_ACTIVITY_WEIGHTS["connection_status"],
        }
        return ranking_results, score_weights
