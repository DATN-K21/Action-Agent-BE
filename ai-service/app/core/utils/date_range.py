from datetime import datetime, timedelta

from app.core.enums import DateRangeEnum


class DateRangeBuilder:
    def __init__(self, reference_date: datetime = datetime.utcnow()):
        self.reference_date = reference_date
        self.start = None
        self.end = None

    def today(self):
        day_start = datetime(self.reference_date.year, self.reference_date.month, self.reference_date.day)
        return day_start, day_start + timedelta(days=1)

    def yesterday(self):
        day_start = datetime(self.reference_date.year, self.reference_date.month, self.reference_date.day)
        yesterday = day_start - timedelta(days=1)
        return yesterday, day_start

    def last_n_days(self, n: int):
        day_start = datetime(self.reference_date.year, self.reference_date.month, self.reference_date.day)
        return day_start - timedelta(days=n - 1), day_start + timedelta(days=1)

    def this_week(self):
        day_start = datetime(self.reference_date.year, self.reference_date.month, self.reference_date.day)
        week_start = day_start - timedelta(days=self.reference_date.weekday())
        return week_start, week_start + timedelta(days=7)

    def this_month(self):
        month_start = datetime(self.reference_date.year, self.reference_date.month, 1)
        if self.reference_date.month == 12:
            month_end = datetime(self.reference_date.year + 1, 1, 1)
        else:
            month_end = datetime(self.reference_date.year, self.reference_date.month + 1, 1)
        return month_start, month_end

    def this_quarter(self):
        month = self.reference_date.month
        quarter_start_month = ((month - 1) // 3) * 3 + 1
        quarter_start = datetime(self.reference_date.year, quarter_start_month, 1)
        if quarter_start_month == 10:
            quarter_end = datetime(self.reference_date.year + 1, 1, 1)
        else:
            quarter_end = datetime(self.reference_date.year, quarter_start_month + 3, 1)
        return quarter_start, quarter_end

    def this_year(self):
        year_start = datetime(self.reference_date.year, 1, 1)
        year_end = datetime(self.reference_date.year + 1, 1, 1)
        return year_start, year_end

    def all_time(self):
        return None, None


def _get_previous_reference_date(period: DateRangeEnum, reference_date: datetime) -> datetime:
    """Calculate the reference date for the previous period."""
    if period == DateRangeEnum.DAY:
        # For "today", previous period is "yesterday" -> shift reference by 1 day
        return reference_date - timedelta(days=1)
    elif period == DateRangeEnum.YESTERDAY:
        # For "yesterday", previous period is "day before yesterday" -> shift reference by 2 days
        return reference_date - timedelta(days=2)
    elif period == DateRangeEnum.WEEK:
        # For "this week", previous period is "last week" -> shift reference by 7 days
        return reference_date - timedelta(days=7)
    elif period == DateRangeEnum.MONTH:
        # For "this month", previous period is "last month"
        if reference_date.month == 1:
            return reference_date.replace(year=reference_date.year - 1, month=12)
        else:
            return reference_date.replace(month=reference_date.month - 1)
    elif period == DateRangeEnum.QUARTER:
        # For "this quarter", previous period is "last quarter" -> shift by 3 months
        if reference_date.month <= 3:
            return reference_date.replace(year=reference_date.year - 1, month=reference_date.month + 9)
        else:
            return reference_date.replace(month=reference_date.month - 3)
    elif period == DateRangeEnum.YEAR:
        # For "this year", previous period is "last year"
        return reference_date.replace(year=reference_date.year - 1)
    elif period == DateRangeEnum.LAST_7_DAYS:
        # For "last 7 days", previous period is "7 days before that" -> shift by 7 days
        return reference_date - timedelta(days=7)
    elif period == DateRangeEnum.LAST_30_DAYS:
        # For "last 30 days", previous period is "30 days before that" -> shift by 30 days
        return reference_date - timedelta(days=30)
    elif period == DateRangeEnum.ALL_TIME:
        return reference_date
    else:
        return reference_date


# Usage
def get_period_range(
    period: DateRangeEnum = DateRangeEnum.ALL_TIME,
    reference_date: datetime = datetime.utcnow(),
) -> tuple[datetime | None, datetime | None]:
    """
    Get date range for a given period using Builder Pattern.

    Args:
        period: The period enum (defaults to ALL_TIME)
        reference_date: Reference date for calculations (defaults to now)

    Returns:
        Tuple of (start_date, end_date). Returns (None, None) for ALL_TIME.
    """
    # Calculate the reference date for the previous period
    previous_reference_date = _get_previous_reference_date(period, reference_date)

    # Create builder with the previous reference date
    builder = DateRangeBuilder(previous_reference_date)

    range_methods = {
        DateRangeEnum.DAY: builder.today,
        DateRangeEnum.YESTERDAY: builder.yesterday,
        DateRangeEnum.WEEK: builder.this_week,
        DateRangeEnum.MONTH: builder.this_month,
        DateRangeEnum.QUARTER: builder.this_quarter,
        DateRangeEnum.YEAR: builder.this_year,
        DateRangeEnum.LAST_7_DAYS: lambda: builder.last_n_days(7),
        DateRangeEnum.LAST_30_DAYS: lambda: builder.last_n_days(30),
        DateRangeEnum.ALL_TIME: builder.all_time,
    }

    method = range_methods.get(period)
    return method() if method else (None, None)

def get_previous_period_range(
    period: DateRangeEnum = DateRangeEnum.ALL_TIME,
    reference_date: datetime = datetime.utcnow(),
) -> tuple[datetime | None, datetime | None]:
    """
    Get previous date range for a given period using Builder Pattern.

    Args:
        period: The period enum (defaults to ALL_TIME)
        reference_date: Reference date for calculations (defaults to now)

    Returns:
        Tuple of (start_date, end_date). Returns (None, None) for ALL_TIME.
    """
    previous_reference_date = reference_date
    builder = DateRangeBuilder(previous_reference_date)

    previous_range_methods = {
        DateRangeEnum.DAY: lambda: builder.yesterday(),
        DateRangeEnum.YESTERDAY: lambda: builder.last_n_days(2),
        DateRangeEnum.WEEK: lambda: builder.this_week(),
        DateRangeEnum.MONTH: lambda: builder.this_month(),
        DateRangeEnum.QUARTER: lambda: builder.this_quarter(),
        DateRangeEnum.YEAR: lambda: builder.this_year(),
        DateRangeEnum.LAST_7_DAYS: lambda: builder.last_n_days(14),
        DateRangeEnum.LAST_30_DAYS: lambda: builder.last_n_days(60),
        DateRangeEnum.ALL_TIME: builder.all_time,
    }

    method = previous_range_methods.get(period)
    return method() if method else (None, None)


def get_period_days(period: DateRangeEnum, reference_date: datetime = datetime.utcnow()) -> int:
    """Get the number of days in the period for average calculations."""
    start_date, end_date = get_period_range(period, reference_date)

    if start_date is None or end_date is None:
        return 1  # For ALL_TIME, return 1 to avoid division by zero

    return (end_date - start_date).days