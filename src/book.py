import uuid
import pandas as pd
from datetime import datetime
from dateutil import tz
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src.models import Base, Booking, Occasion, Answer


class Database():
    def __init__(self):
        self.bookingcolumns = ('booking_id', 'next_occasion', 'title', 'time_created', 'description', 'location')
        self.occasioncolumns = ('booking_id', 'occasion', 'date', 'time_start', 'time_end')
        self.answercolumns = ('booking_id', 'occasion', 'name', 'answer')

        self.engine = create_engine("sqlite+pysqlite:///data/tables.db")
        Base.metadata.create_all(self.engine)
        self.model_from_columns = {
            self.bookingcolumns: Booking,
            self.occasioncolumns: Occasion,
            self.answercolumns: Answer,
            }

    def add(self, source_df: pd.DataFrame):
        Table = self.model_from_columns[tuple(source_df.columns)]
        rows = [Table(**dict(x[1])) for x in source_df.iterrows()]
        with Session(self.engine) as session:
            session.add_all(rows)
            session.commit()

    def new(self, booking_id):
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        new_booking = pd.DataFrame(
            {k: [v] for k, v in zip(self.bookingcolumns, [booking_id, 0, "", time_created, "", ""])}
            )
        self.add(new_booking)

    def update(self, variables: dict, selection: dict, Table):
        with Session(self.engine) as session:
            row = session.execute(select(Table).filter_by(**selection)).scalar_one()
            for column, value in variables.items():
                setattr(row, column, value)
            session.commit()

    def update_bookings(self, variables: dict, selection: dict):
        self.update(variables, selection, Booking)

    def update_answers(self, variables: dict, selection: dict):
        self.update(variables, selection, Answer)

    def get(self, columns, booking_id=''):
        Table = self.model_from_columns[columns]
        with Session(self.engine) as session:
            if booking_id != '':
                rows = [x[0] for x in session.execute(select(Table).filter_by(booking_id=booking_id)).all()]
            else:
                rows = session.query(Table).all()
        data = [[getattr(row, col) for row in rows] for col in columns]
        df = pd.DataFrame(dict(zip(columns, data)))
        return df

    def get_bookings(self, booking_id=''):
        return self.get(self.bookingcolumns, booking_id)

    def get_occasions(self, booking_id=''):
        return self.get(self.occasioncolumns, booking_id)

    def get_answers(self, booking_id=''):
        return self.get(self.answercolumns, booking_id)

    def get_occasion(self, booking_id):
        booking = self.get_bookings(booking_id)
        occasion = int(booking['next_occasion'].iloc[0])
        self.update_bookings({'next_occasion': occasion + 1}, {'booking_id': booking_id})
        return occasion

    def get_booking(self, booking_id):
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
        self.replace_bool = {False: '', True: '\u2713'}
        self.db = Database()

    def new_context(self):
        self.booking_id = str(uuid.uuid1())
        self.db.new(self.booking_id)

    def set_context(self, booking_id):
        self.booking_id = booking_id

    def update_bookings(self, title, description, location):
        update_items = {'title': title, 'description': description, 'location': location}
        selection = {'booking_id': self.booking_id}
        self.db.update_bookings(update_items, selection)

    def add_occasion(self, date, time_start, time_end):
        occasion = self.db.get_occasion(self.booking_id)
        new_occasion = pd.DataFrame(
            {k: [v] for k, v in zip(self.db.occasioncolumns, [self.booking_id, occasion, date, time_start, time_end])}
            )
        self.db.add(new_occasion)

    def add_answer(self, occasion, name, answer):
        new_answer = pd.DataFrame(
            {k: [v] for k, v in zip(self.db.answercolumns, [self.booking_id, occasion, name, answer])}
            )
        self.db.add(new_answer)

    def update_answer(self, occasion, name, answer):
        update_items = {'answer': answer}
        selection = {'occasion': occasion, 'name': name, 'booking_id': self.booking_id}
        self.db.update_answers(update_items, selection)

    def to_local_time(self, time):
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Stockholm')
        utc = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=from_zone)
        local = utc.astimezone(to_zone).replace(microsecond=0).strftime('%Y-%m-%d %H:%M')
        return local

    def weekday(self, date):
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

    def to_table(self, edit_name=''):
        occasions = self.db.get_occasions(self.booking_id)
        answers = self.db.get_answers(self.booking_id)
        names = list(answers.name.unique())
        wanted_columns = ['date', 'time_start', 'time_end']
        wanted_columns.extend(names)
        header = [self.columns_translation.get(x, x) for x in wanted_columns]
        if edit_name in header:
            header.remove(edit_name)
        header.insert(0, '')
        rows = []
        edit_answers = []
        for occasion in occasions.iterrows():
            occasion = occasion[1].to_dict()
            row = [occasion[x] for x in wanted_columns[:3]]
            for name in wanted_columns[3:]:
                occasion_loc = (answers.occasion == occasion['occasion'])
                name_loc = (answers.name == name)
                answer = answers.loc[occasion_loc & name_loc, ['answer']]
                if len(answer):
                    answer = answer.iloc[0, 0]
                else:
                    answer = False
                if name == edit_name:
                    edit_answers.append(answer)
                else:
                    row.extend([answer])
            row = [self.replace_bool.get(x, x) for x in row]
            row = ['' if str(x) == 'nan' else x for x in row]
            row.insert(0, self.weekday(row[0]))
            rows.append(row)
        table = {'header': header, 'rows': rows}
        table.update(self.db.get_booking(self.booking_id))
        table['names'] = names
        table['edit_name'] = edit_name
        table['edit_answers'] = edit_answers
        return table

    def index_list(self, n=5):
        bookings_raw = self.db.get_bookings().sort_values(by='time_created', ascending=False).head(n).iterrows()
        bookings_list = []
        for booking in bookings_raw:
            booking = booking[1].to_dict()
            bookings_list.append({
                'booking_id': booking['booking_id'],
                'title': booking['title'],
                'time_created': self.to_local_time(booking['time_created']),
                'description': booking['description'],
                })
        return bookings_list

    def occasions_list(self):
        return list(self.db.get_occasions(self.booking_id).occasion)

    def names_list(self):
        return list(self.db.get_answers(self.booking_id).name)
