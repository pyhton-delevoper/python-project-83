import psycopg2
import requests
import os
from bs4 import BeautifulSoup
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
        error = [('alert-danger', 'Некорректный URL')]
        return render_template('analyze.html', message=error, wrong_url=url)

    parsed_url = urlparse(url)
    normal_url = parsed_url.scheme + '://' + parsed_url.netloc
    with connect.cursor() as cur:
        cur.execute('SELECT id FROM urls WHERE name = %s;', [normal_url])
        url_id = cur.fetchone()

        if url_id:
            flash('Страница уже существует', 'alert-info')
            return redirect(url_for('watch_url', id=url_id[0]), 200)

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
            status_code = requests.get(url, timeout=1).status_code
            status_code == requests.codes.ok
        except Exception:
            flash('Произошла ошибка при проверке', 'alert-danger')
            return redirect(url_for('watch_url', id=id))
        html = requests.get(url).text
        soup = BeautifulSoup(html, features="html.parser")
        h1 = soup.h1.string
        title = soup.title.string
        desc = soup.find('meta', attrs={'name': 'description'})['content']
        cur.execute('''
                INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s);
                ''', [id, status_code, h1, title, desc, created_at])
        connect.commit()
    flash('Страница успешно проверена', 'alert-success')
    return redirect(url_for('watch_url', id=id), 302)


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000)
