import uuid
from datetime import datetime
from dateutil import tz
from pandas import DataFrame
from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session
from src.models import Base, Booking, Occasion, Answer, Comment, Active
from typing import Tuple, List


class Database():
    def __init__(self):
        self.bookingcolumns = ('booking_id', 'next_occasion', 'title', 'time_created', 'description', 'location')
        self.occasioncolumns = ('booking_id', 'occasion', 'date', 'time_start', 'time_end')
        self.answercolumns = ('booking_id', 'occasion', 'name', 'answer')
        self.commentcolumns = ('booking_id', 'time_created', 'name', 'comment')
        self.activecolumns = ('booking_id', 'is_active')

        self.engine = create_engine("sqlite+pysqlite:///data/tables.db")
        Base.metadata.create_all(self.engine)
        self.model_from_columns = {
            self.bookingcolumns: Booking,
            self.occasioncolumns: Occasion,
            self.answercolumns: Answer,
            self.commentcolumns: Comment,
            self.activecolumns: Active,
            }

    def add(self, source_df: DataFrame) -> None:
        Table = self.model_from_columns[tuple(source_df.columns)]
        rows = [Table(**dict(x[1])) for x in source_df.iterrows()]
        with Session(self.engine) as session:
            session.add_all(rows)
            session.commit()

    def new(self, booking_id: str) -> None:
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        new_booking = DataFrame(
            {k: [v] for k, v in zip(self.bookingcolumns, [booking_id, 0, "", time_created, "", ""])}
            )
        self.add(new_booking)

    def update(self, variables: dict, selection: dict, Table: Base) -> None:
        with Session(self.engine) as session:
            row = session.execute(select(Table).filter_by(**selection)).scalar_one_or_none()
            if row is None:
                _ = session.execute(insert(Table).values(**selection))
                session.commit()
                row = session.execute(select(Table).filter_by(**selection)).scalar_one()
            for column, value in variables.items():
                setattr(row, column, value)
            session.commit()

    def update_bookings(self, variables: dict, selection: dict) -> None:
        self.update(variables, selection, Booking)

    def update_answers(self, variables: dict, selection: dict) -> None:
        self.update(variables, selection, Answer)

    def update_active(self, variables: dict, selection: dict) -> None:
        self.update(variables, selection, Active)

    def get(self, columns: Tuple[str], booking_id: str = '') -> DataFrame:
        Table = self.model_from_columns[columns]
        with Session(self.engine) as session:
            if booking_id != '':
                rows = [x[0] for x in session.execute(select(Table).filter_by(booking_id=booking_id)).all()]
            else:
                rows = session.query(Table).all()
        data = [[getattr(row, col) for row in rows] for col in columns]
        df = DataFrame(dict(zip(columns, data)))
        return df

    def get_bookings(self, booking_id: str = '') -> DataFrame:
        return self.get(self.bookingcolumns, booking_id)

    def get_occasions(self, booking_id: str = '') -> DataFrame:
        return self.get(self.occasioncolumns, booking_id)

    def get_answers(self, booking_id: str = '') -> DataFrame:
        return self.get(self.answercolumns, booking_id)

    def get_comments(self, booking_id: str = '') -> DataFrame:
        return self.get(self.commentcolumns, booking_id)

    def get_active(self, booking_id: str = '') -> DataFrame:
        return self.get(self.activecolumns, booking_id)

    def get_occasion(self, booking_id: str) -> int:
        booking = self.get_bookings(booking_id)
        occasion = int(booking['next_occasion'].iloc[0])
        self.update_bookings({'next_occasion': occasion + 1}, {'booking_id': booking_id})
        return occasion

    def get_booking(self, booking_id: str) -> dict:
        bookings = self.get_bookings()
        details = bookings.loc[bookings.booking_id == booking_id].to_dict('records')[0]
        return details


class BookingManager():
    def __init__(self):
        self.booking_id = ""
        self.columns_translation = {
            'date': 'Datum',
            'time_start': 'Från',
            'time_end': 'Till',
            }
        self.replace_int = {0: '', 1: '\u2713', 2: '?'}
        self.db = Database()

    def new_context(self) -> None:
        self.booking_id = str(uuid.uuid1())
        self.db.new(self.booking_id)

    def set_context(self, booking_id: str) -> None:
        self.booking_id = booking_id

    def update_bookings(self, title: str, description: str, location: str) -> None:
        update_items = {'title': title, 'description': description, 'location': location}
        selection = {'booking_id': self.booking_id}
        self.db.update_bookings(update_items, selection)

    def add_occasion(self, date: str, time_start: str, time_end: str) -> None:
        occasion = self.db.get_occasion(self.booking_id)
        new_occasion = DataFrame(
            {k: [v] for k, v in zip(self.db.occasioncolumns, [self.booking_id, occasion, date, time_start, time_end])}
            )
        self.db.add(new_occasion)

    def add_occasions(self, dates: List[str], start_times: List[str], end_times: List[str]) -> None:
        for occasion in zip(dates, start_times, end_times):
            self.add_occasion(occasion[0], occasion[1], occasion[2])

    def add_answer(self, occasion: int, name: str, answer: int) -> None:
        new_answer = DataFrame(
            {k: [v] for k, v in zip(self.db.answercolumns, [self.booking_id, occasion, name, answer])}
            )
        self.db.add(new_answer)

    def add_answers(self, occasions: List[int], name: str, answers: List[int]) -> None:
        for occasion, answer in zip(occasions, answers):
            self.add_answer(occasion, name, answer)

    def update_answer(self, occasion: int, name: str, answer: int) -> None:
        update_items = {'answer': answer}
        selection = {'occasion': occasion, 'name': name, 'booking_id': self.booking_id}
        self.db.update_answers(update_items, selection)

    def update_answers(self, occasions: List[int], name: str, answers: List[int]) -> None:
        for occasion, answer in zip(occasions, answers):
            self.update_answer(occasion, name, answer)

    def add_comment(self, name: str, comment: str) -> None:
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        new_comment = DataFrame(
            {k: [v] for k, v in zip(self.db.commentcolumns, [self.booking_id, time_created, name, comment])}
            )
        self.db.add(new_comment)

    def is_active(self, booking_id: str = '') -> bool:
        if booking_id == '':
            booking_id = self.booking_id
        result = self.db.get_active(booking_id).get('is_active')
        if len(result) > 0:
            is_active = result[0]
        else:
            is_active = True
        return is_active

    def update_active(self, is_active: bool) -> None:
        update_items = {'is_active': is_active}
        selection = {'booking_id': self.booking_id}
        self.db.update_active(update_items, selection)

    def set_active(self, set_inactive: List[str]) -> None:
        booking_is_active = not (len(set_inactive) == 1 and set_inactive[0] != 'False')
        self.update_active(booking_is_active)

    def to_local_time(self, time: str) -> str:
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Stockholm')
        utc = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=from_zone)
        local = utc.astimezone(to_zone).replace(microsecond=0).strftime('%Y-%m-%d %H:%M')
        return local

    def weekday(self, date: str) -> str:
        weekdays = [
            "Måndag",
            "Tisdag",
            "Onsdag",
            "Torsdag",
            "Fredag",
            "Lördag",
            "Söndag"
            ]
        if date != '':
            i = datetime.strptime(date, '%Y-%m-%d').weekday()
            weekday = weekdays[i]
        else:
            weekday = ''
        return weekday

    def to_table(self, edit_name: str = '') -> dict:
        comments = self.db.get_comments(self.booking_id).sort_values(by=['time_created'])
        comments = list(zip(
            list(comments['name']),
            [self.to_local_time(x) for x in list(comments['time_created'])],
            list(comments['comment']),
            ))

        answers = self.db.get_answers(self.booking_id)

        occasion_columns = ['date', 'time_start', 'time_end']
        names = list(answers['name'].unique())
        show_header = ['']
        show_header.extend([self.columns_translation[x] for x in occasion_columns])
        show_header.append('#')
        for name in names:
            if name != edit_name:
                show_header.append(name)

        answer_header = [v for i, v in enumerate(show_header) if i != show_header.index('#')]

        show_rows = []
        answer_rows = []
        edit_answers = []
        ranks = []

        occasions = self.db.get_occasions(self.booking_id).sort_values(by=['date', 'time_start'])

        answers_copy = answers.copy()
        answers_copy['answer'] = answers_copy['answer'].apply(lambda x: int(x == 1))
        answers_sum = answers_copy.groupby(by=['occasion']).sum()
        best_occasions = DataFrame({
            'occasion': list(answers_sum.index),
            'checked': list(answers_sum['answer'])
            })
        best_occasions['rank'] = list(best_occasions.rank(method='dense', ascending=False)['checked'].astype(int))

        for occasion in occasions.iterrows():
            occasion = occasion[1].to_dict()
            row = [occasion[x] for x in occasion_columns]
            occasion_vote = best_occasions[best_occasions['occasion'] == occasion['occasion']]
            if len(occasion_vote) > 0:
                n_yes = occasion_vote['checked'].iloc[0]
                rank = occasion_vote['rank'].iloc[0]
                row.append(f'{str(n_yes)}/{str(len(names))}')
            else:
                row.append('')
                rank = 0
            ranks.append(rank)

            occasion_loc = (answers['occasion'] == occasion['occasion'])

            for name in names:
                name_loc = (answers['name'] == name)
                answer = answers.loc[occasion_loc & name_loc, ['answer']]
                if len(answer):
                    answer = answer.iloc[0, 0]
                else:
                    answer = 0
                if name == edit_name:
                    edit_answers.append(answer)
                else:
                    row.extend([answer])

            row = [self.replace_int.get(x, x) for x in row]
            row.insert(0, self.weekday(row[0]))

            show_rows.append(row)
            answer_rows.append([v for i, v in enumerate(row) if i != show_header.index('#')])

        booking = self.db.get_booking(self.booking_id)

        table = {
            'booking_id': booking['booking_id'],
            'title': booking['title'],
            'time_created': self.to_local_time(booking['time_created']),
            'location': booking['location'],
            'description': booking['description'],
            'header': {'show': show_header, 'answer': answer_header},
            'rows': {'show': show_rows, 'answer': answer_rows},
            'names': names,
            'edit_name': edit_name,
            'edit_answers': edit_answers,
            'ranks': ranks,
            'comments': comments,
            'is_active': self.is_active()
            }

        return table

    def index_list(self, n: int = 10) -> List[dict]:
        bookings_raw = self.db.get_bookings().sort_values(by='time_created', ascending=False).iterrows()
        bookings_list = []
        i = 1
        for booking in bookings_raw:
            if i > n:
                break
            booking = booking[1].to_dict()
            if not self.is_active(booking['booking_id']):
                continue
            bookings_list.append({
                'booking_id': booking['booking_id'],
                'title': booking['title'],
                'time_created': self.to_local_time(booking['time_created']),
                'description': booking['description'],
                })
            i += 1
        return bookings_list

    def occasions_list(self) -> List[int]:
        return list(self.db.get_occasions(self.booking_id).sort_values(by=['date', 'time_start']).occasion)

    def names_list(self) -> List[str]:
        return list(self.db.get_answers(self.booking_id).name)
