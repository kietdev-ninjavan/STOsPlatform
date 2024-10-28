from datetime import datetime, timedelta

from django.utils import timezone

from ..models import Holiday


class DateHelper:
    """
    A utility class for handling date-related operations such as checking for holidays, weekends,
    and retrieving available or locked dates.
    """

    def is_date_locked(self, date: datetime) -> bool:
        """
        Check if the given date is locked due to being a holiday or a weekend.

        Args:
            date (datetime): The date to check.

        Returns:
            bool: True if the date is locked, False otherwise.
        """
        return self.is_holiday(date) or self.is_weekend(date)

    @staticmethod
    def is_holiday(date: datetime) -> bool:
        """
        Check if the given date is a holiday.

        Args:
            date (datetime): The date to check.

        Returns:
            bool: True if the date is a holiday, False otherwise.
        """
        return Holiday.objects.filter(date=date).exists()

    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """
        Check if the given date falls on a weekend (Sunday).

        Args:
            date (datetime): The date to check.

        Returns:
            bool: True if the date is a weekend (Sunday), False otherwise.
        """
        return date.weekday() == 6  # Sunday is represented by 6 in Python's weekday method

    def is_today_locked(self) -> bool:
        """
        Check if today's date is locked.

        Returns:
            bool: True if today is locked, False otherwise.
        """
        today = timezone.now()
        return self.is_date_locked(today)

    def get_next_unlocked_date(self, start_date: datetime = None) -> datetime:
        """
        Get the next available date that is not locked.

        Args:
            start_date (datetime, optional): The starting date to check. Defaults to None (today).

        Returns:
            datetime: The next available date that is not a holiday or a weekend.
        """
        if start_date is None:
            start_date = timezone.now()

        while self.is_date_locked(start_date):
            start_date += timedelta(days=1)
        return start_date

    def get_nth_unlocked_date(self, num_days: int, start_date: datetime = None) -> datetime:
        """
        Get the date that is 'num_days' unlocked days from the given starting date, skipping locked dates.

        Args:
            num_days (int): The number of unlocked days to advance.
            start_date (datetime, optional): The starting date. Defaults to None (today).

        Returns:
            datetime: The calculated date that is 'num_days' unlocked days from the start date.
        """
        if start_date is None:
            start_date = timezone.now()

        while num_days > 0:
            start_date += timedelta(days=1)
            if not self.is_date_locked(start_date):
                num_days -= 1
        return start_date

    def get_locked_dates_between(self, from_date: datetime, to_date: datetime = None) -> list:
        """
        Get a list of locked dates (holidays or weekends) within a given date range.

        Args:
            from_date (datetime): The start date for the range.
            to_date (datetime, optional): The end date for the range. Defaults to today.

        Returns:
            list: A list of datetime objects representing locked dates within the range.
        """
        if to_date is None:
            to_date = timezone.now()

        from_date = datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0)
        date_range = [from_date]

        while from_date < to_date:
            from_date += timedelta(days=1)
            if from_date.date() != to_date.date():
                date_range.append(from_date)

        return [date for date in date_range if self.is_date_locked(date)]

    def get_previous_working_day(self, date: datetime = None) -> datetime:
        """
        Get the previous working day from the given date, skipping holidays and weekends.

        Args:
            date (datetime, optional): The reference date. Defaults to today.

        Returns:
            datetime: The previous working day that is not a holiday or weekend.
        """
        if date is None:
            date = timezone.now()

        previous_date = date - timedelta(days=1)
        while self.is_date_locked(previous_date):
            previous_date -= timedelta(days=1)
        return previous_date
