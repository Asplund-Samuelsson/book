import secrets

from flask import Flask, render_template, request, url_for, flash, redirect

from src.book import Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

b = Booking()


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
    if request.method == 'POST':
        title = request.form['title']
        location = request.form.get('location', '')
        description = request.form['description']
        dates = request.form.getlist('dates')
        start_times = request.form.getlist('start_times')
        end_times = request.form.getlist('end_times')

        if not title:
            flash('Titel krävs.')
        else:
            b.new()
            b.update_title(title)
            b.update_description(description)
            b.update_location(location)
            for occasion in zip(dates, start_times, end_times):
                b.add_occasion(occasion[0], occasion[1], occasion[2])
            b.save()
            return redirect(url_for('show', identifier=b.identifier))

    return render_template('create.html')

@app.route('/show/<identifier>')
def show(identifier):
    b.load(identifier)
    return render_template('show.html', booking=b.to_table())

@app.route('/answer/<identifier>', methods=['GET', 'POST'])
def answer(identifier):
    b.load(identifier)

    if request.method == 'POST':
        name = request.form['name']
        answers = request.form.getlist('answers')

        if not name:
            flash('Namn krävs.')
        else:
            for i, answer in enumerate(answers):
                n = list(b.booking.index)[i]
                b.add_answer(n, name, answer is not None)
            b.save()
            return redirect(url_for('show', identifier=b.identifier))

    return render_template('answer.html', booking=b.to_table())
