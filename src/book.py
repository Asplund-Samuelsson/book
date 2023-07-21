import uuid
import pandas as pd
import sqlite3
from contextlib import closing
from datetime import datetime
from dateutil import tz
from pathlib import Path


class Database():
    def __init__(self):
        # SQL
        self.databasefile = Path("data/tables.db")
        self.schemafile = Path("src/schema.sql")

        if not self.databasefile.is_file():
            self.init_db()

        with closing(self.connect_db()) as db:
            def columns(table):
                cursor = db.execute(f'select * from {table} limit 1;')
                return tuple(x[0] for x in cursor.description)
            self.bookings_columns = columns('bookings')
            self.occasions_columns = columns('occasions')
            self.answers_columns = columns('answers')
            self.table_from_columns = {
                self.bookings_columns: 'bookings',
                self.occasions_columns: 'occasions',
                self.answers_columns: 'answers',
            }
            self.columns_from_table = {v: k for k, v in self.table_from_columns.items()}

        # CSV
        self.bookingfile = Path("data/bookings.csv")
        self.bookingcolumns = ('booking_id', 'occasions', 'title', 'time_created', 'description', 'location')
        self.occasionfile = Path("data/occasions.csv")
        self.occasioncolumns = ('booking_id', 'occasion', 'date', 'time_start', 'time_end')
        self.answerfile = Path("data/answers.csv")
        self.answercolumns = ('booking_id', 'occasion', 'name', 'answer')
        self.file_from_columns = {
            self.bookingcolumns: self.bookingfile,
            self.occasioncolumns: self.occasionfile,
            self.answercolumns: self.answerfile,
        }
        self.columns_from_file = {v: k for k, v in self.file_from_columns.items()}
        self.column_types = {
            'booking_id': str,
            'occasion_id': int,
            'answer_id': int,
            'occasions': int,
            'occasion': int,
            'title': str,
            'time_created': str,
            'description': str,
            'location': str,
            'name': str,
            'answer': bool,
        }

    def connect_db(self):
        return sqlite3.connect(self.databasefile)

    def init_db(self):
        with closing(self.connect_db()) as db:
            with open(self.schemafile, 'r') as schema:
                db.cursor().executescript(schema.read())
            db.commit()

    def cast_types(self, df: pd.DataFrame):
        return df.astype({k: v for k, v in self.column_types.items() if k in df.columns})

    def load(self, file: Path):
        if file.is_file():
            df = pd.read_csv(file).fillna('')
        else:
            df = pd.DataFrame({column: [] for column in self.columns_from_file(file)})
        return df

    def modify(self, source_df: pd.DataFrame, add=False):
        # TODO What if multiple users modify at the same time?
        target = self.file_from_columns[tuple(source_df.columns)]
        if add:
            target_df = self.load(target)
            target_df = pd.concat([target_df, source_df])
        else:
            target_df = source_df
        target_df = self.cast_types(target_df)
        target_df.to_csv(target, index=False)

    def add(self, source_df: pd.DataFrame):
        self.modify(source_df, add=True)

    def update(self, source_df: pd.DataFrame):
        self.modify(source_df)

    def new(self, booking_id):
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        new_booking = pd.DataFrame(
            {k: [v] for k, v in zip(self.bookingcolumns, [booking_id, 0, "", time_created, "", ""])}
            )
        self.add(new_booking)

    def update_bookings(self, variables: dict, booking_id):
        bookings = self.get_bookings()
        for column, value in variables.items():
            bookings.loc[bookings.booking_id == booking_id, [column]] = value
        self.update(bookings)

    def get(self, file, booking_id=''):
        df = self.load(file)
        if booking_id != '':
            df = df.loc[df.booking_id == booking_id]
        return self.cast_types(df)

    def get_bookings(self, booking_id=''):
        return self.get(self.bookingfile, booking_id)

    def get_occasions(self, booking_id=''):
        return self.get(self.occasionfile, booking_id)

    def get_answers(self, booking_id=''):
        return self.get(self.answerfile, booking_id)

    def get_occasion(self, booking_id):
        booking = self.get_bookings(booking_id)
        occasion = booking['occasions'].iloc[0]
        self.update_bookings({'occasions': occasion + 1}, booking_id)
        return occasion

    def get_booking(self, booking_id):
        bookings = self.get_bookings()
        details = bookings.loc[bookings.booking_id == booking_id].to_dict('records')[0]
        return details


class Booking():
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
        self.db.update_bookings(update_items, self.booking_id)

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
        i = datetime.strptime(date, '%Y-%m-%d').weekday()
        return weekdays[i]

    def to_table(self, names=True):
        occasions = self.db.get_occasions(self.booking_id)
        answers = self.db.get_answers(self.booking_id)
        wanted_columns = ['date', 'time_start', 'time_end']
        if names:
            wanted_columns.extend(list(answers.name.unique()))
        header = [self.columns_translation.get(x, x) for x in wanted_columns]
        header.insert(0, '')
        rows = []
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
                row.extend([answer])
            row = [self.replace_bool.get(x, x) for x in row]
            row = ['' if str(x) == 'nan' else x for x in row]
            row.insert(0, self.weekday(row[0]))
            rows.append(row)
        table = {'header': header, 'rows': rows}
        table.update(self.db.get_booking(self.booking_id))
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
