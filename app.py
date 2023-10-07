import secrets
import os

from flask import Flask, render_template, request, url_for, flash, redirect
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from src.book import BookingManager

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

b = BookingManager()

login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Logga in för att visa sidan.'


class User(UserMixin):
    def check_password(self, password):
        return password == os.getenv('PASSWORD')

    def get_id(self):
        return 1


user = User()


@login.user_loader
def load_user(user_id):
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        if not user.check_password(request.form['password']):
            flash('Fel lösenord.')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html', bookings=b.index_list())


@app.route('/create/', defaults={'booking_id': ''}, methods=('GET', 'POST'))
@app.route('/create/<booking_id>', methods=('GET', 'POST'))
@login_required
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
@login_required
def show(booking_id):
    b.set_context(booking_id)
    return render_template('show.html', booking=b.to_table(), booking_id=booking_id)


@app.route('/answer/<booking_id>', defaults={'edit_name': ''}, methods=['GET', 'POST'])
@app.route('/answer/<booking_id>/<edit_name>', methods=['GET', 'POST'])
@login_required
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
    booking['tristates'] = ['\u274C', '\u2705', '\u2753']
    booking['tristate_answers'] = [booking['tristates'][x] for x in booking['edit_answers']]

    if request.method == 'POST':
        comment = request.form['comment']
        if not edit:
            name = request.form['name']
        else:
            name = edit_name
        occasions = b.occasions_list()
        answers = [booking['tristates'].index(x) for x in request.form.getlist('tristate_answers')]

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
            if comment != '':
                b.add_comment(name, comment)
            return redirect(url_for('show', booking_id=booking_id))

    return render_template('answer.html', booking=booking, edit=edit)


@app.route('/comment/<booking_id>', methods=['GET', 'POST'])
@login_required
def comment(booking_id):
    b.set_context(booking_id)

    if request.method == 'POST':
        name = request.form['name']
        comment = request.form['comment']

        if not name:
            flash('Namn krävs.')
        elif not comment:
            flash('Kommentarsfältet kan inte vara tomt.')
        else:
            b.add_comment(name, comment)
            return redirect(url_for('show', booking_id=booking_id))

    return render_template('comment.html', booking=b.to_table())
