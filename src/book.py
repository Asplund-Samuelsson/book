import uuid
import pandas as pd
from datetime import datetime
from dateutil import tz
from pathlib import Path


class Booking():
    def __init__(self):
        self.identifier = ""
        self.bookingfile = Path("data/bookings.csv")
        self.bookingcolumns = ['identifier', 'occasions', 'title', 'time_created', 'description', 'location']
        self.occasionfile = Path("data/occasions.csv")
        self.occasioncolumns = ['identifier', 'occasion', 'date', 'start_time', 'end_time']
        self.answerfile = Path("data/answers.csv")
        self.answercolumns = ['identifier', 'occasion', 'name', 'answer']
        self.columns_translation = {
            'date': 'Datum',
            'start_time': 'Från',
            'end_time': 'Till',
            }
        self.replace_bool = {False: '', True: '\u2713'}
        if self.bookingfile.is_file():
            self.bookings = pd.read_csv(self.bookingfile)
        else:
            self.bookings = pd.DataFrame({k: [] for k in self.bookingcolumns})

    def new(self):
        time_created = datetime.utcnow().replace(microsecond=0).isoformat()
        self.identifier = str(uuid.uuid1())
        self.bookings.loc[len(self.bookings)] = [self.identifier, 0, "", time_created, "", ""]
        self.booking = pd.DataFrame({column: [] for column in self.occasioncolumns})
        self.answers = pd.DataFrame({column: [] for column in self.answercolumns})

    def update_title(self, title):
        self.bookings.loc[self.bookings.identifier == self.identifier, ['title']] = title

    def update_description(self, description):
        self.bookings.loc[self.bookings.identifier == self.identifier, ['description']] = description

    def update_location(self, location):
        self.bookings.loc[self.bookings.identifier == self.identifier, ['location']] = location

    def file(self, identifier):
        return f"data/{identifier}.csv"

    def commit(self, source, target):
        target_df = pd.read_csv(target)
        target_df = target_df.loc[target_df.identifier != self.identifier]
        target_df = pd.concat(target_df, source)
        target_df.to_csv(target, index=False)

    def save(self):
        # TODO What if multiple users save at the same time?
        self.commit(self.booking, self.occasionfile)
        self.commit(self.answers, self.answerfile)
        self.bookings.to_csv(self.bookingfile, index=False)

    def load(self, identifier):
        self.identifier = identifier
        df = pd.read_csv(self.occasionfile)
        self.booking = df.loc[df.identifier == self.identifier]
        df = pd.read_csv(self.answerfile)
        self.answers = df.loc[df.identifier == self.identifier]

    def add_occasion(self, date, start_time, end_time):
        last_row = len(self.booking)
        occasion = self.bookings.loc[self.bookings.identifier == self.identifier, ['occasions']]
        self.bookings.loc[self.bookings.identifier == self.identifier, ['occasions']] += 1
        self.booking.loc[last_row] = [self.identifier, occasion, date, start_time, end_time]
        self.booking = self.booking.sort_values(by=['date', 'start_time', 'end_time'])

    def add_answer(self, occasion, name, answer):
        last_row = len(self.answers)
        self.answers.loc[last_row] = [self.identifier, occasion, name, answer]

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
        wanted_columns = ['date', 'start_time', 'end_time']
        if names:
            wanted_columns.extend(list(self.answers.name.unique()))
        header = [self.columns_translation.get(x, x) for x in wanted_columns]
        header.insert(0, '')
        rows = []
        for occasion in self.booking.iterrows():
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
        table.update(self.bookings.loc[self.bookings.identifier == self.identifier].to_dict('records')[0])
        return table

    def index_list(self, n=5):
        bookings_raw = self.bookings.sort_values(by='time_created', ascending=False).head(n).iterrows()
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
