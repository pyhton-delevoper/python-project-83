import psycopg2
import os
from dotenv import load_dotenv
from flask import (Flask,
                   render_template,
                   url_for)


app = Flask(__name__)
app.secret_key = load_dotenv('SECRET_KEY')

db_url = os.getenv('DATABASE_URL')
connect = psycopg2.connect(db_url)


@app.get('/')
def start_page():
    return render_template('start.html')
