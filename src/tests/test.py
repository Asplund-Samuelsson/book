import pandas as pd
from importlib import reload
import src.book

reload(src.book)
b = src.book.Booking()

b.new()
b.save()

b.load(next(iter(b.metadata)))

b.add_occasion("2023-07-22", "12:00", "12:30")
b.add_occasion("2023-07-20", "18:30", "19:00")

b.add_person('PersonA')

b.add_answer(1, 'PersonA', True)
b.add_answer(0, 'PersonA', True)
b.add_answer(1, 'PersonA', False)

b.add_person('PersonÖ')

b.add_answer(0, 'PersonÖ', True)

b.save()

b = src.book.Booking()

b.load(next(iter(b.metadata)))

b.new()
b.add_occasion("2023-08-30", "10:00", "18:00")
b.save()

b.update_title('Test')
b.update_description('something')
b.update_location('there')

b.save()

b = src.book.Booking()
b.load(next(iter(b.metadata)))
