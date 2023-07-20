import uuid
import pandas as pd
from datetime import datetime
from dateutil import tz
from pathlib import Path


class Database():
    def __init__(self):
        self.bookingfile = Path("data/bookings.csv")
        self.bookingcolumns = ('identifier', 'occasions', 'title', 'time_created', 'description', 'location')
        self.occasionfile = Path("data/occasions.csv")
        self.occasioncolumns = ('identifier', 'occasion', 'date', 'time_start', 'time_end')
        self.answerfile = Path("data/answers.csv")
        self.answercolumns = ('identifier', 'occasion', 'name', 'answer')
        self.file_from_columns = {
            self.bookingcolumns: self.bookingfile,
            self.occasioncolumns: self.occasionfile,
            self.answercolumns: self.answerfile
        }
        self.columns_from_file = {v: k for k, v in self.file_from_columns.items()}
        self.column_types = {
            'identifier': str,
            'occasions': int,
            'occasion': int,
            'title': str,
            'time_created': str,
            'description': str,
            'location': str,
            'name': str,
            'answer': bool
        }

    def new(self, identifier):
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        new_booking = pd.DataFrame(
            {k: [v] for k, v in zip(self.bookingcolumns, [identifier, 0, "", time_created, "", ""])}
            )
        self.add(new_booking)

    def update_bookings(self, variables: dict, identifier):
        bookings = self.get_bookings()
        for column, value in variables.items():
            bookings.loc[bookings.identifier == identifier, [column]] = value
        self.update(bookings)

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

    def get_bookings(self):
        df = self.load(self.bookingfile)
        bookings = self.cast_types(df)
        return bookings

    def get_occasions(self, identifier):
        df = self.load(self.occasionfile)
        occasions = self.cast_types(df.loc[df.identifier == identifier])
        return occasions

    def get_answers(self, identifier):
        df = self.load(self.answerfile)
        answers = self.cast_types(df.loc[df.identifier == identifier])
        return answers

    def get_occasion(self, identifier):
        bookings = self.get_bookings()
        occasion = bookings.loc[bookings.identifier == identifier, ['occasions']].iloc[0, 0]
        bookings.loc[bookings.identifier == identifier, ['occasions']] += 1
        self.update(bookings)
        return occasion

    def booking_details(self, identifier):
        bookings = self.get_bookings()
        details = bookings.loc[bookings.identifier == identifier].to_dict('records')[0]
        return details


class Booking():
    def __init__(self):
        self.identifier = ""
        self.columns_translation = {
            'date': 'Datum',
            'time_start': 'Från',
            'time_end': 'Till',
            }
        self.replace_bool = {False: '', True: '\u2713'}
        self.db = Database()

    def new(self):
        self.identifier = str(uuid.uuid1())
        self.db.new(self.identifier)

    def load(self, identifier):
        self.identifier = identifier

    def update_bookings(self, title, description, location):
        update_items = {'title': title, 'description': description, 'location': location}
        self.db.update_bookings(update_items, self.identifier)

    def add_occasion(self, date, time_start, time_end):
        occasion = self.db.get_occasion(self.identifier)
        new_occasion = pd.DataFrame(
            {k: [v] for k, v in zip(self.db.occasioncolumns, [self.identifier, occasion, date, time_start, time_end])}
            )
        self.db.add(new_occasion)

    def add_answer(self, occasion, name, answer):
        new_answer = pd.DataFrame(
            {k: [v] for k, v in zip(self.db.answercolumns, [self.identifier, occasion, name, answer])}
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
        occasions = self.db.get_occasions(self.identifier)
        answers = self.db.get_answers(self.identifier)
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
        table.update(self.db.booking_details(self.identifier))
        return table

    def index_list(self, n=5):
        bookings_raw = self.db.get_bookings().sort_values(by='time_created', ascending=False).head(n).iterrows()
        bookings_list = []
        for booking in bookings_raw:
            booking = booking[1].to_dict()
            bookings_list.append({
                'identifier': booking['identifier'],
                'title': booking['title'],
                'time_created': self.to_local_time(booking['time_created']),
                'description': booking['description'],
                })
        return bookings_list
