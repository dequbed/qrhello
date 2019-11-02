from flask import Flask

from dbfoo import Sqlite

import db_dsn

app = Flask(__name__)

db = Sqlite(db_dsn.sqlite_file)


from qrhello import routes

