import psycopg2
import os
from dotenv import load_dotenv, dotenv_values
from urllib.parse import urlparse, urlunparse
from validators.url import url as valid_url
from datetime import date
from flask import (Flask,
                   render_template,
                   url_for,
                   request,
                   flash,
                   get_flashed_messages,
                   redirect)


app = Flask(__name__)
a = load_dotenv('SECRET_KEY')
print(a)

db_url = os.getenv('DATABASE_URL')
connect = psycopg2.connect(db_url)


@app.route('/')
def start_page():
    messages = get_flashed_messages(with_categories=True)
    return render_template('start.html', messages=messages)


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'GET':
        with connect.cursor() as cur:
            data = cur.execute('SELECT * FROM urls ORDER BY created_at;')
            return render_template('show_urls.html', data=data)
    url = request.form.get('url')
    parsed_url = urlparse(url)
    normal_url = urlunparse(parsed_url)
    if not valid_url(normal_url):
        flash('Некорректный URL', 'failed')
        return render_template
    with connect.cursor() as cur:
        cur.execute('INSERT INTO urls (name, created_at) VALUES (%s, %s);',
            (normal_url[:3], date.today()))
    connect.commit()
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for(watch_url)), 200
    


@app.route('/urls/<id>')
def watch_url(id):
    with connect.cursor() as cur:
        cur.execute('SELECT * FROM urls WHERE id = %s;', id,)
        data = cur.fetchone()
        if not data:
            return render_template('no_such_url.html',
                    message='Здесь нет того, что вы ищите')
    return render_template('watch_url.html', data=data)
