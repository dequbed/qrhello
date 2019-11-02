from flask import Flask

from dbfoo import Sqlite

import qrhello.db_dsn as dsn

app = Flask(__name__)

db = Sqlite(dsn.sqlite_file)


from qrhello import routes

