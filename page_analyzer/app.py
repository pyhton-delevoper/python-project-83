from flask import Flask


app = Flask(__name__)


app.route('/')
def start_page():
    return 'hello'


def main():
    pass


if __name__ == '__main__':
    main()


__all__ = ['app']