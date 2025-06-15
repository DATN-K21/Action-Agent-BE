from datetime import datetime

from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.db_models.user import User
from app.schemas.statistics import UserStatisticsResponse


async def get_user_statistics(session: SessionDep) -> UserStatisticsResponse:
    # Get the first day of this month
    now = datetime.utcnow()
    first_day_of_this_month = datetime(now.year, now.month, 1)

    stmt = select(
        func.count(User.id).filter(User.is_deleted.is_(False)).label("total"),
        func.count(User.id).filter(User.is_deleted.is_(False), User.created_at < first_day_of_this_month).label("last_month_total"),
    )
    result = await session.execute(stmt)
    row = result.one()
    total_users = row.total
    last_month_total = row.last_month_total

    # Calculate average per day (over 30 days)
    avg_per_day = total_users / 30 if total_users > 0 else 0

    # Calculate percentage change compared to last month
    if last_month_total == 0:
        percentage_change = "1000.0+" if total_users > 0 else "0.0%"
    else:
        percentage_change = f"{((total_users - last_month_total) / last_month_total) * 100:.1f}%"

    return UserStatisticsResponse(total=total_users, avg_per_day=avg_per_day, percentage_change=percentage_change)
