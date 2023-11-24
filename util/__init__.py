from datetime import datetime
from typing import overload, Literal, Any
from beanie.odm.queries.find import FindMany

from core.db_model import GroupMessageLog
from core.model import TimeRange, DataSource

from .time_tools import get_time_ranges


@overload
async def get_message(
    source: DataSource, source_id: str | int, time_range: TimeRange, format_time: Literal[False]
) -> list[tuple[datetime, FindMany[GroupMessageLog]]]:
    ...


@overload
async def get_message(
    source: DataSource, source_id: str | int, time_range: TimeRange, format_time: Literal[True]
) -> list[tuple[str, FindMany[GroupMessageLog]]]:
    ...


async def get_message(
    source: DataSource, source_id: str | int, time_range: TimeRange, format_time: bool = False
) -> list[tuple[Any, FindMany[GroupMessageLog]]]:
    time_ranges = get_time_ranges(time_range)
    data = []
    format_map = {
        TimeRange.DAY: "%H:00",
        TimeRange.WEEK: "%m-%d",
        TimeRange.MONTH: "%m-%d",
        TimeRange.YEAR: "%Y-%m",
    }

    for start_time, end_time in time_ranges:
        query = GroupMessageLog.find_many(
            start_time <= GroupMessageLog.log_time,
            GroupMessageLog.log_time < end_time
        )
        if source == DataSource.SELF:
            query = query.find_many(GroupMessageLog.qid == str(source_id))
        elif source == DataSource.GROUP:
            query = query.find_many(GroupMessageLog.group_id == str(source_id))

        if format_time:
            data.append((start_time.strftime(format_map[time_range]), query))
        else:
            data.append((start_time, query))

    return data
