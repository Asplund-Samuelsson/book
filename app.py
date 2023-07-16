from flask import Flask, render_template, request, url_for, flash, redirect

from src.book import Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = 'CRDFY3AhXQ6QwEqwXKkyH6UGmcn3heSN'

b = Booking()


def make_index_list():
    bookings = []
    for identifier in b.metadata:
        booking = b.metadata[identifier]
        booking = {
            'title': booking['title'],
            'description': booking['description'],
            }
        bookings.append(booking)
    return bookings


@app.route('/')
def index():
    return render_template('index.html', bookings=make_index_list())


@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        location = request.form.get('location', '')
        description = request.form['description']

        if not title:
            flash('Title is required!')
        elif not description:
            flash('description is required!')
        else:
            b.new()
            b.update_title(title)
            b.update_description(description)
            b.update_location(location)
            b.save()
            return redirect(url_for('index'))

    return render_template('create.html')
