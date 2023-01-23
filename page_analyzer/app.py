import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url as valid_url
from datetime import datetime
from flask import (Flask,
                   render_template,
                   url_for,
                   request,
                   flash,
                   get_flashed_messages,
                   redirect)


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

db_url = os.getenv('DATABASE_URL')
connect = psycopg2.connect(db_url)


@app.route('/')
def analyze_url():
    messages = get_flashed_messages(with_categories=True)
    url = ''
    return render_template('analyze.html', messages=messages, wrong_url=url)


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'GET':
        with connect.cursor() as cur:
            cur.execute('SELECT * FROM urls ORDER BY created_at;')
            data = cur.fetchall()
        return render_template('show_urls.html', data=data)

    url = request.form.get('url')
    if not valid_url(url):
        message = [('alert-danger', 'Некорректный URL')]
        return render_template('analyze.html', message=message, wrong_url=url)

    parsed_url = urlparse(url)
    normal_url = parsed_url.scheme + '://' + parsed_url.netloc
    with connect.cursor() as cur:
        cur.execute('SELECT id FROM urls WHERE name = %s;', [normal_url])
        url_id = cur.fetchone()[0]

        if url_id:
            flash('Такой адрес уже существует', 'alert-info')
            return redirect(url_for('watch_url', id=url_id))

        created_at = datetime.now()
        cur.execute('INSERT INTO urls (name, created_at) VALUES (%s, %s);',
                    [normal_url, created_at.date()])
    flash('Страница успешно добавлена', 'alert-success')
    return redirect(url_for('watch_url', id=url_id))


@app.route('/urls/<int:id>')
def watch_url(id):
    with connect.cursor() as cur:
        cur.execute('SELECT * FROM urls WHERE id = %s;', [id])
        data = cur.fetchone()
    message = get_flashed_messages(with_categories=True)
    return render_template('watch_url.html', data=data, message=message)
