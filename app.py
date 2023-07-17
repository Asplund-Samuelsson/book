import secrets

from flask import (
    Flask,
    render_template,
    request,
    url_for,
    flash,
    redirect,
    )
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import (
    StringField,
    DateField,
    TimeField,
    SubmitField,
    FormField,
    FieldList,
    )
from wtforms.validators import DataRequired, Length

from src.book import Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

b = Booking()


class OccasionEntryForm(FlaskForm):
    date = DateField('')
    start_time = TimeField('')
    end_time = TimeField('')


class BookingForm(FlaskForm):
    title = StringField(
        'Titel', validators=[DataRequired()], render_kw={'placeholder': 'Vad ska bokas?'})
    location = StringField(
        'Plats', render_kw={'placeholder': 'Plats för bokningen'})
    description = StringField(
        'Beskrivning', validators=[Length(15, 60)], render_kw={'placeholder': 'Beskrivning av bokningen'})
    occasions = FieldList(FormField(OccasionEntryForm), min_entries=1)
    submit = SubmitField('Spara')


def make_index_list(n=5):
    bookings_raw = sorted(b.metadata.items(), key=lambda x: x[1]['time_created'], reverse=True)
    bookings = []
    for booking in bookings_raw:
        bookings.append({
            'identifier': booking[0],
            'title': booking[1]['title'],
            'time_created': b.to_local_time(booking[1]['time_created']),
            'description': booking[1]['description'],
            })
    return bookings[:n]


@app.route('/')
def index():
    return render_template('index.html', bookings=make_index_list())


@app.route('/create/', methods=('GET', 'POST'))
def create():
    form = BookingForm()
    if request.method == 'POST':
        title = request.form['title']
        location = request.form.get('location', '')
        description = request.form['description']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        if not title:
            flash('Titel krävs.')
        elif not date:
            flash('Datum krävs.')
        else:
            b.new()
            b.update_title(title)
            b.update_description(description)
            b.update_location(location)
            b.add_occasion(date, start_time, end_time)
            b.save()
            return redirect(url_for('show', identifier=b.identifier))

    return render_template('create.html', form=form)

@app.route('/show/<identifier>')
def show(identifier):
    b.load(identifier)
    return render_template('show.html', booking=b.to_table())
