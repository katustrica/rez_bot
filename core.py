from collections import defaultdict
from datetime import time
from time import strptime

import psycopg2

from core_static import TIME_INTERVALS, Days, HourType, WeekInfo

DATABASE_URL = r'postgres://njjzezeeaagpoj:e162814183baab2fc7a7bc1c4a095c2f7f6eb24aa56323611ad74544c6ec9c7f@ec2-34-233-214-228.compute-1.amazonaws.com:5432/d46a4kne6pqgvc'  # oDATABASE_URL = r'postgres://njjzezeeaagpoj:e162814183baab2fc7a7bc1c4a095c2f7f6eb24aa56323611ad74544c6ec9c7f@ec2-34-233-214-228.compute-1.amazonaws.com:5432/d46a4kne6pqgvc'  # os.environ['DATABASE_URL']
# DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')


def days() -> list[str]:
    return tuple(day.value.title() for day in Days)


def hours() -> list[str]:
    return tuple(f'{times[0]:%H:%M} - {times[1]:%H:%M}' for times in TIME_INTERVALS)


def hour_types() -> list[str]:
    return tuple(a.name.title() for a in HourType)


class Teacher():
    def __init__(self, id: int):
        self.id = id

    def get_week_info_string(self, time_type: HourType) -> str:
        header_str = f'--------------\n{time_type.name.title()} время\n--------------\n'
        week = self.get_week_info(time_type)
        week_dict = defaultdict(list)
        for day in week:
            week_dict[day.day].append(f'{day.from_time:%H:%M} - {day.to_time:%H:%M}')

        for day, hours in week_dict.items():
            header_str += day + '\n' + '\n'.join(hours) + '\n\n'
        return header_str

    def get_week_info(self, time_type: int | None = None) -> tuple[WeekInfo]:
        """
        Вернуть календарь с часами по дням. 1 - занято, 2 - отдых, 0 - свободно.
        """
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                  t_id,
                  CASE day_num
                    WHEN 1 THEN 'Понедельник'
                    WHEN 2 THEN 'Вторник'
                    WHEN 3 THEN 'Среда'
                    WHEN 4 THEN 'Четверг' 
                    WHEN 5 THEN 'Пятница' 
                    WHEN 6 THEN 'Суббота' 
                    WHEN 7 THEN 'Воскресенье'
                  END day_str,
                  from_time,
                  to_time,
                  time_type,
                  s_id
                FROM 
                  week 
                WHERE 
                  t_id = %(t_id)s
                  AND (%(type)s IS NULL OR time_type = %(type)s)
                ORDER BY
                  day_num,
                  from_time;
            """, {'t_id': self.id, 'type': time_type})
            conn.commit()
            return tuple(WeekInfo(*record) for record in cur)

    def update_week_info(self, day: int, hours: str, type: int) -> None:
        """
        Вернуть календарь с часами по дням. 1 - занято, 2 - отдых, 0 - свободно.
        """
        with conn.cursor() as cur:
            for hour in hours:
                from_time, to_time = tuple(
                    time(strptime(h, '%H:%M').tm_hour, strptime(h, '%H:%M').tm_min) for h in hour.split(' - ')
                )
                cur.execute(
                    '''
                    INSERT INTO 
                      week(day_num, t_id, from_time, to_time, time_type)
                    VALUES
                      (%(day)s, %(t_id)s, %(from_time)s, %(to_time)s, %(type)s) 
                    ON CONFLICT ON CONSTRAINT week_pk 
                    DO 
                       UPDATE SET time_type = %(type)s
                    ''',
                    {'day': day, 'from_time': from_time, 'to_time': to_time, 'type': type, 't_id': self.id}
                )
        self.selected_day = None
        self.selected_time = None
        self.selected_type = None
        conn.commit()

    @property
    def selected_day(self):
        with conn.cursor() as cur:
            cur.execute('SELECT selected_day FROM teacher WHERE id = (%s)', (self.id,))
            conn.commit()
            return cur.fetchone()[0]

    @selected_day.setter
    def selected_day(self, selected_day):
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE teacher SET selected_day = %(selected_day)s WHERE id = %(t_id)s RETURNING selected_day',
                {'t_id': self.id, 'selected_day': selected_day}
            )
            conn.commit()

    @property
    def selected_time(self):
        with conn.cursor() as cur:
            cur.execute('SELECT selected_time FROM teacher WHERE id = (%s)', (self.id,))
            conn.commit()
            return cur.fetchone()[0]

    @selected_time.setter
    def selected_time(self, selected_time: str):
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE teacher SET selected_time = %(selected_time)s WHERE id = %(t_id)s RETURNING selected_time',
                {'t_id': self.id, 'selected_time': selected_time}
            )
            conn.commit()

    @property
    def selected_type(self):
        with conn.cursor() as cur:
            cur.execute('SELECT selected_type FROM teacher WHERE id = (%s)', (self.id,))
            conn.commit()
            return cur.fetchone()[0]

    @selected_type.setter
    def selected_type(self, selected_type: str):
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE teacher SET selected_type = %(selected_type)s WHERE id = %(t_id)s RETURNING selected_type',
                {'t_id': self.id, 'selected_type': selected_type}
            )
            conn.commit()