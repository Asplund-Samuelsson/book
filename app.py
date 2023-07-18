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
    return render_template('show.html', booking=b.to_table(), identifier=b.identifier)


@app.route('/answer/<identifier>', methods=['GET', 'POST'])
def answer(identifier):
    b.load(identifier)

    if request.method == 'POST':
        name = request.form['name']
        true_answers = [int(x) for x in request.form.getlist('answers')]
        answers = [x in true_answers for x in range(len(b.booking))]

        if not name:
            flash('Namn krävs.')
        else:
            for i in range(len(b.booking)):
                b.add_answer(i, name, answers[i])
            b.save()
            return redirect(url_for('show', identifier=b.identifier))

    return render_template('answer.html', booking=b.to_table())
