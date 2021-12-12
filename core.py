from enum import Enum, IntEnum
import json

class HourType(IntEnum):
    СВОБОДНОЕ = 0
    ЗАНЯТОЕ = 1
    ОТДЫХ = 2


week_info = dict[str, dict[str, int]]


class Rezeda():
    __file_name = 'week.json'
    _days = None
    _hours = None
    selected_day = None
    selected_hour = None
    selected_type = None

    @property
    def days(self) -> list[str]:
        if not self._days:
            week = self.get_week_info()
            self._days = tuple(week.keys())
        return self._days

    @property
    def hours(self) -> list[str]:
        if not self._hours:
            week = self.get_week_info()
            self._hours = tuple(tuple(week.values())[0].keys())
        return self._hours

    def get_info(self) -> str:
        week = self.get_week_info()
        free_time = self.get_time(HourType.СВОБОДНОЕ, week)
        # relax_time = self.get_time(HourType.ОТДЫХ, week)
        return '\n\n'.join([free_time])

    def get_week_info(self) -> week_info:
        """
        Вернуть календарь с часами по дням. 1 - занято, 2 - отдых, 0 - свободно.
        """
        with open(self.__file_name, 'r', encoding='utf8') as week_json:
            return json.load(week_json)

    def update_week_info(self, day, hour, type) -> None:
        """
        Вернуть календарь с часами по дням. 1 - занято, 2 - отдых, 0 - свободно.
        """
        week = self.get_week_info()
        week[day][hour] = int(type)
        with open(self.__file_name, 'w', encoding='utf8') as week_json:
            return json.dump(week, week_json, ensure_ascii=False, indent=4)

    def get_time(self, time_type: HourType, week: week_info) -> str:
        header_str = f'--------------\n{time_type.name.title()} время\n--------------\n'
        for day, hours_dict in week.items():
            hours = [hour for hour, hour_type in hours_dict.items() if hour_type == time_type]
            if hours:
                header_str += day + '\n' + '\n'.join(hours) + '\n\n'
        return header_str