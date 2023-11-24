import time
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from core.model import TimeRange


class TimeRecorder:
    def __init__(self):
        self.time = time.time()

    def _rec(self):
        return int((time.time() - self.time) * 1000)

    def total(self):
        return calc_time_total(self._rec())


def calc_time_total(t):
    if t < 5000:
        return f"{t}毫秒"

    time_delta = timedelta(seconds=int(t / 1000))
    day = time_delta.days
    hour, mint, sec = tuple(int(n) for n in str(time_delta).split(",")[-1].split(":"))

    total = ""
    if day:
        total += "%d天" % day
    if hour:
        total += "%d小时" % hour
    if mint:
        total += "%d分钟" % mint
    if sec and not day and not hour:
        total += "%d秒" % sec

    return total


def get_time_ranges(
    time_range: TimeRange, now: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))
) -> list[tuple[datetime, datetime]]:
    now = now.replace(minute=0, second=0, microsecond=0)

    delta_params = {
        TimeRange.DAY: ("hours", 24, None, {"hours": 1}),
        TimeRange.WEEK: ("days", 7, {"hour": 0}, {"days": 1}),
        TimeRange.MONTH: ("days", 30, {"hour": 0}, {"days": 1}),
        TimeRange.YEAR: ("months", 12, {"day": 1, "hour": 0}, {"months": 1}),
    }
    delta_param, num_units, additional_reset, increment = delta_params[time_range]

    time_ranges = []
    for i in range(num_units):
        start_time = now - relativedelta(**{delta_param: i})
        if additional_reset:
            start_time = start_time.replace(**additional_reset)
        end_time = start_time + relativedelta(**increment)
        time_ranges.append((start_time, end_time))

    return time_ranges
