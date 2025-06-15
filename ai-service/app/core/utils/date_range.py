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

    builder = DateRangeBuilder(reference_date)

    range_methods = {
        DateRangeEnum.DAY: builder.today,
        DateRangeEnum.YESTERDAY: builder.yesterday,
        DateRangeEnum.WEEK: builder.this_week,
        DateRangeEnum.MONTH: builder.this_month,
        DateRangeEnum.LAST_7_DAYS: lambda: builder.last_n_days(7),
        DateRangeEnum.LAST_30_DAYS: lambda: builder.last_n_days(30),
        DateRangeEnum.ALL_TIME: builder.all_time,
    }

    method = range_methods.get(period)
    return method() if method else (None, None)
