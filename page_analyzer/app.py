import psycopg2
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators.url import url as valid_url
from werkzeug.exceptions import HTTPException
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


@app.errorhandler(HTTPException)
def handle_bad_request(e):
    return render_template('404.html'), 404


@app.route('/')
def analyze_url():
    messages = get_flashed_messages(with_categories=True)
    url = ''
    return render_template('analyze.html', messages=messages, wrong_url=url)


@app.route('/urls', methods=['GET', 'POST'])
def show_urls():
    if request.method == 'GET':
        with connect.cursor() as cur:
            cur.execute('''
                    select urls.id, name, max(url_checks.created_at)
                    as created_at, status_code from urls
                    left join url_checks on urls.id = url_id
                    group by urls.id, urls.name, status_code
                    order by id;
                ''')
            data = cur.fetchall()
        return render_template('show_urls.html', data=data)

    url = request.form.get('url')
    if not valid_url(url):
        error = [('alert-danger', 'Некорректный URL')]
        return render_template('analyze.html', message=error, wrong_url=url)

    parsed_url = urlparse(url)
    normal_url = parsed_url.scheme + '://' + parsed_url.netloc
    with connect.cursor() as cur:
        cur.execute('SELECT id FROM urls WHERE name = %s;', [normal_url])
        url_id = cur.fetchone()

        if url_id:
            flash('Страница уже существует', 'alert-info')
            return redirect(url_for('watch_url', id=url_id[0]), 302)

        created_at = datetime.now().date()
        cur.execute('INSERT INTO urls (name, created_at) VALUES (%s, %s);',
                    [normal_url, created_at])
        connect.commit()
        cur.execute('SELECT id FROM urls WHERE name = %s;', [normal_url])
        url_id = cur.fetchone()[0]
    flash('Страница успешно добавлена', 'alert-success')
    return redirect(url_for('watch_url', id=url_id), 302)


@app.route('/urls/<int:id>')
def watch_url(id):
    with connect.cursor() as cur:
        cur.execute('SELECT * FROM urls WHERE id = %s;', [id])
        data = cur.fetchone()
        cur.execute('''SELECT * FROM url_checks WHERE url_id = %s
                       ORDER BY id DESC;''', [id])
        checks = cur.fetchall()
    message = get_flashed_messages(with_categories=True)
    return render_template(
               'watch_url.html', data=data, checks=checks, message=message
            )


@app.post('/urls/<int:id>/checks')
def check_url(id):
    created_at = datetime.now().date()
    with connect.cursor() as cur:
        cur.execute('SELECT name FROM urls WHERE id = %s;', [id])
        url = cur.fetchone()[0]
        try:
            response = requests.get(url, timeout=1)
            response.raise_for_status()
        except Exception:
            flash('Произошла ошибка при проверке', 'alert-danger')
            return redirect(url_for('watch_url', id=id), 302)
        status_code = response.status_code
        html = response.text
        soup = BeautifulSoup(html, features="html.parser")
        h1 = soup.h1.text if soup.h1 else ''
        title = soup.title.text if soup.title else ''
        desc = soup.find('meta', attrs={'name': 'description'})
        desc = desc.get('content') if desc else ''
        cur.execute('''
                INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s);
                ''', [id, status_code, h1, title, desc, created_at])
        connect.commit()
    flash('Страница успешно проверена', 'alert-success')
    return redirect(url_for('watch_url', id=id), 302)
