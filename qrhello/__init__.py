from flask import Flask

from dbfoo import Sqlite

app = Flask(__name__)
# db = Sqlite('/var/lib/qrhello/db.sqlite')
db = Sqlite('/tmp/db.sqlite')


from qrhello import routes

