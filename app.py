import secrets

from flask import Flask, render_template, request, url_for, flash, redirect

from src.book import BookingManager

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

b = BookingManager()


@app.route('/')
def index():
    return render_template('index.html', bookings=b.index_list())


@app.route('/create/', defaults={'booking_id': ''}, methods=('GET', 'POST'))
@app.route('/create/<booking_id>', methods=('GET', 'POST'))
def create(booking_id):
    edit = booking_id != ''
    b.set_context(booking_id)
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
            if not edit:
                b.new_context()
            b.update_bookings(title, description, location)
            if not edit:
                for occasion in zip(dates, start_times, end_times):
                    b.add_occasion(occasion[0], occasion[1], occasion[2])
            return redirect(url_for('show', booking_id=b.booking_id))

    if not edit:
        booking = {}
    else:
        booking = b.to_table()
    return render_template('create.html', booking=booking, edit=edit)


@app.route('/show/<booking_id>')
def show(booking_id):
    b.set_context(booking_id)
    return render_template('show.html', booking=b.to_table(), booking_id=booking_id)


@app.route('/answer/<booking_id>', defaults={'edit_name': ''}, methods=['GET', 'POST'])
@app.route('/answer/<booking_id>/<edit_name>', methods=['GET', 'POST'])
def answer(booking_id, edit_name):
    edit = edit_name != ''
    b.set_context(booking_id)

    booking = b.to_table(edit_name)
    i = booking['header'].index('#')
    booking['header'].pop(i)
    rows = []
    for row in booking['rows']:
        row.pop(i)
        rows.append(row)
    booking['rows'] = rows

    if request.method == 'POST':
        if not edit:
            name = request.form['name']
        else:
            name = edit_name
        occasions = b.occasions_list()
        true_answers = [occasions[int(x)] for x in request.form.getlist('answers')]
        answers = [x in true_answers for x in occasions]

        if not name:
            flash('Namn krävs.')
        elif name in b.names_list() and not edit:
            flash('Namnet är redan registrerat.')
        else:
            for occasion, answer in zip(occasions, answers):
                if not edit:
                    b.add_answer(occasion, name, answer)
                else:
                    b.update_answer(occasion, name, answer)
            return redirect(url_for('show', booking_id=booking_id))

    return render_template('answer.html', booking=booking, edit=edit)


@app.route('/comment/<booking_id>', methods=['GET', 'POST'])
def comment(booking_id):
    b.set_context(booking_id)

    if request.method == 'POST':
        name = request.form['name']
        comment = request.form['comment']

        if not comment:
            flash('Kommentarsfältet kan inte vara tomt.')
        else:
            b.add_comment(name, comment)
            return redirect(url_for('show', booking_id=booking_id))

    return render_template('comment.html', booking=b.to_table())
