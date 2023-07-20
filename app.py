import secrets

from flask import Flask, render_template, request, url_for, flash, redirect

from src.book import Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

b = Booking()


@app.route('/')
def index():
    return render_template('index.html', bookings=b.index_list())


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
            b.update_bookings(title, description, location)
            for occasion in zip(dates, start_times, end_times):
                b.add_occasion(occasion[0], occasion[1], occasion[2])
            return redirect(url_for('show', identifier=b.identifier))

    return render_template('create.html')


@app.route('/show/<identifier>')
def show(identifier):
    b.load(identifier)
    return render_template('show.html', booking=b.to_table(), identifier=b.identifier)


@app.route('/answer/<identifier>', methods=['GET', 'POST'])
def answer(identifier):
    b.load(identifier)

    if request.method == 'POST':
        name = request.form['name']
        occasions = b.occasions_list()
        true_answers = [occasions[int(x)] for x in request.form.getlist('answers')]
        answers = [x in true_answers for x in occasions]

        if not name:
            flash('Namn krävs.')
        elif name in b.names_list():
            flash('Namnet är redan registrerat.')
        else:
            for occasion, answer in zip(occasions, answers):
                b.add_answer(occasion, name, answer)
            return redirect(url_for('show', identifier=identifier))

    return render_template('answer.html', booking=b.to_table())
