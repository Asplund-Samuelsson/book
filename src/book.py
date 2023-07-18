import json
import uuid
import pandas as pd
from datetime import datetime
from dateutil import tz
from pathlib import Path


class Booking():
    def __init__(self):
        self.metafile = Path("data/metadata.json")
        self.identifier = ""
        self.columns = ['date', 'start_time', 'end_time']
        self.columns_translation = {
            'date': 'Datum',
            'start_time': 'Från',
            'end_time': 'Till',
            }
        self.replace_bool = {False: '', True: '\u2713'}
        if self.metafile.is_file():
            with open(self.metafile) as m:
                self.metadata = json.loads(m.read())
        else:
            self.metadata = dict()

    def new(self):
        self.identifier = str(uuid.uuid1())
        self.metadata[self.identifier] = {
            "title": "",
            "time_created": datetime.utcnow().replace(microsecond=0).isoformat(),
            "description": "",
            "location": "",
            }
        self.booking = pd.DataFrame({column: [] for column in self.columns})

    def update_title(self, title):
        self.metadata[self.identifier]['title'] = title

    def update_description(self, description):
        self.metadata[self.identifier]['description'] = description

    def update_location(self, location):
        self.metadata[self.identifier]['location'] = location

    def file(self, identifier):
        return f"data/{identifier}.csv"

    def save(self):
        # TODO What if multiple users save at the same time?
        self.booking.to_csv(self.file(self.identifier), index=False)
        with open(self.metafile, 'w') as m:
            m.write(json.dumps(self.metadata, indent=2))

    def load(self, identifier):
        self.identifier = identifier
        self.booking = pd.read_csv(self.file(identifier))

    def add_occasion(self, date, start_time, end_time):
        last_row = len(self.booking.index)
        self.booking.loc[last_row] = [date, start_time, end_time]
        self.booking = self.booking.sort_values(by=self.columns)

    def add_person(self, name):
        self.booking[name] = pd.Series([False]*len(self.booking))

    def add_answer(self, index, name, answer):
        self.booking.loc[index, name] = answer

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
        wanted_columns = self.booking.columns if names else self.columns
        header = [self.columns_translation.get(x, x) for x in wanted_columns]
        header.insert(0, '')
        rows = []
        for row in self.booking.iterrows():
            row = row if names else row[:len(self.columns)]
            row = [self.replace_bool.get(x, x) for x in row[1]]
            row = ['' if str(x) == 'nan' else x for x in row]
            row.insert(0, self.weekday(row[0]))
            rows.append(row)
        table = {'header': header, 'rows': rows}
        table.update(self.metadata[self.identifier])
        return table
