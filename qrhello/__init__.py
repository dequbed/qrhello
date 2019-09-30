from flask import Flask

from qrhello.dbfoo import Sqlite

app = Flask(__name__)
db = Sqlite('/tmp/db.sqlite')

from qrhello import routes

