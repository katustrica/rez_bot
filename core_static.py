from enum import IntEnum, Enum
from dataclasses import dataclass
from datetime import datetime, time

TIME_INTERVALS = sum(
    (((time(hour, 0), time(hour, 30)), (time(hour, 30), time(hour+1, 0))) for hour in range(9, 22)), ()
)


class Days(Enum):
    monday = 'понедельник'
    tuesday = 'вторник'
    wednesday = 'среда'
    thursday = 'четверг'
    friday = 'пятница'
    saturday = 'суббота'
    sunday = 'воскресенье'


class HourType(IntEnum):
    СВОБОДНОЕ = 0
    ЗАНЯТОЕ = 1
    ОТДЫХ = 2


@dataclass
class TeacherInfo:
    id: int
    fio: str
    mobile: str | None
    telegram: str | None
    license: bool
    last_active: datetime
    selected_day: str | None
    selected_time: datetime | None
    selected_type: int | None


@dataclass
class WeekInfo:
    t_id: int
    day: str
    from_time: time
    to_time: time
    type: int
    s_id: int | None
