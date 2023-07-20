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
        self.targets = {
            self.bookingcolumns: self.bookingfile,
            self.occasioncolumns: self.occasionfile,
            self.answercolumns: self.answerfile
        }
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
        if self.bookingfile.is_file():
            self.bookings = self.read_csv(self.bookingfile)
        else:
            self.bookings = pd.DataFrame({k: [] for k in self.bookingcolumns})
        self.bookings = self.cast_types(self.bookings)

    def read_csv(self, file):
        return pd.read_csv(file).fillna('')

    def new(self, identifier):
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        new_booking = pd.DataFrame(
            {k: [v] for k, v in zip(self.bookingcolumns, [identifier, 0, "", time_created, "", ""])}
            )
        self.bookings = pd.concat([self.bookings, new_booking])

    def update_title(self, title, identifier):
        self.bookings.loc[self.bookings.identifier == identifier, ['title']] = title

    def update_description(self, description, identifier):
        self.bookings.loc[self.bookings.identifier == identifier, ['description']] = description

    def update_location(self, location, identifier):
        self.bookings.loc[self.bookings.identifier == identifier, ['location']] = location

    def cast_types(self, df):
        return df.astype({k: v for k, v in self.column_types.items() if k in df.columns})

    def anti_join(self, df1, df2):
        # https://stackoverflow.com/a/55543744
        outer = df1.merge(df2, how='outer', indicator=True)
        anti_join = outer[(outer._merge == 'left_only')].drop('_merge', axis=1)
        return anti_join

    def commit(self, source):
        # TODO What if multiple users save at the same time?
        target = self.targets[tuple(source.columns)]
        target_df = self.read_csv(target)
        source_df = self.anti_join(source, target_df)
        target_df = pd.concat([target_df, source_df])
        target_df = self.cast_types(target_df)
        target_df.to_csv(target, index=False)

    def load_occasions(self, identifier):
        df = self.read_csv(self.occasionfile)
        occasions = self.cast_types(df.loc[df.identifier == identifier])
        return occasions

    def load_answers(self, identifier):
        df = self.read_csv(self.answerfile)
        answers = self.cast_types(df.loc[df.identifier == identifier])
        return answers

    def get_occasion(self, identifier):
        occasion = self.bookings.loc[self.bookings.identifier == identifier, ['occasions']].iloc[0, 0]
        self.bookings.loc[self.bookings.identifier == identifier, ['occasions']] += 1
        return occasion

    def booking_details(self, identifier):
        details = self.bookings.loc[self.bookings.identifier == identifier].to_dict('records')[0]
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
        self.occasions = pd.DataFrame({column: [] for column in self.db.occasioncolumns})
        self.answers = pd.DataFrame({column: [] for column in self.db.answercolumns})

    def save(self):
        self.db.commit(self.occasions)
        self.db.commit(self.answers)
        self.db.commit(self.db.bookings)

    def load(self, identifier):
        self.identifier = identifier
        self.occasions = self.db.load_occasions(identifier)
        self.answers = self.db.load_answers(identifier)

    def update_bookings(self, title, description, location):
        self.db.update_title(title, self.identifier)
        self.db.update_description(description, self.identifier)
        self.db.update_location(location, self.identifier)

    def add_occasion(self, date, time_start, time_end):
        occasion = self.db.get_occasion(self.identifier)
        new_occasion = pd.DataFrame(
            {k: [v] for k, v in zip(self.occasions.columns, [self.identifier, occasion, date, time_start, time_end])}
            )
        self.occasions = pd.concat([self.occasions, new_occasion])
        self.occasions = self.occasions.sort_values(by=['date', 'time_start', 'time_end'])

    def add_answer(self, occasion, name, answer):
        new_answer = pd.DataFrame(
            dict(zip(self.answers.columns, [[self.identifier], [occasion], [name], [answer]]))
            )
        self.answers = pd.concat([self.answers, new_answer])

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
        wanted_columns = ['date', 'time_start', 'time_end']
        if names:
            wanted_columns.extend(list(self.answers.name.unique()))
        header = [self.columns_translation.get(x, x) for x in wanted_columns]
        header.insert(0, '')
        rows = []
        for occasion in self.occasions.iterrows():
            occasion = occasion[1].to_dict()
            row = [occasion[x] for x in wanted_columns[:3]]
            for name in wanted_columns[3:]:
                occasion_loc = (self.answers.occasion == occasion['occasion'])
                name_loc = (self.answers.name == name)
                answer = self.answers.loc[occasion_loc & name_loc, ['answer']]
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
        bookings_raw = self.db.bookings.sort_values(by='time_created', ascending=False).head(n).iterrows()
        bookings = []
        for booking in bookings_raw:
            booking = booking[1].to_dict()
            bookings.append({
                'identifier': booking['identifier'],
                'title': booking['title'],
                'time_created': self.to_local_time(booking['time_created']),
                'description': booking['description'],
                })
        return bookings
