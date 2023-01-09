from flask import Flask
from dotenv import load_dotenv


app = Flask(__name__)

app.secret_key = load_dotenv('SECRET_KEY')


@app.route('/')
def start_page():
    return 'hello'
