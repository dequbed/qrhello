import time
import datetime
import sqlite3
import psycopg2
from influxdb import InfluxDBClient

import qrhello.db_dsn as dsn




class DB:
    #
    # Required functions to implement
    #

    def hello(self, name, email):
        """
        Enters a new User, visiting the lab today.
        :param name:
        :param email:
        :return:
        """
        raise NotImplementedError("'hello' is required to be implemented on a subclass")

    def claim(self, item_id, name, email):
        """
        Claims an item for an user, removing any previous claimant
        """
        raise NotImplementedError("'claim' is required to be implemented on a subclass")

    def return_time(self, item_id, when):
        """
        Marks an item as returned at the specific time
        """
        if not isinstance(when, datetime.datetime):
            raise TypeError("'when' needs to be a datetime object")
        raise NotImplementedError("'return_time' is required to be implemented on a subclass")

    def claimed(self, item_id):
        """
        Returns (name, email) of the person that has the item claimed. None if nobody has the item claimed at the moment.
        """
        raise NotImplementedError("'claimed' is required to be implemented on a subclass")

    def still_claimed(self, name):
        """
        Returns (item_id) of the items, the person has still claimed. None if there is no such item.
        """
        raise NotImplementedError("'still_claimed' is required to be implemented on a subclass")

    #
    # Utility functions which have a default implementation
    #

    def is_claimed(self, item_id):
        """
        Returns 'True' if an item is currently claimed
        """
        self.claimed(item_id) is not None

    def is_free(self, item_id):
        """
        Returns 'True' if an item is currently free
        """
        self.claimed(item_id) is None

    def return_now(self, item_id):
        """
        Returns an item
        """
        self.return_time(item_id, datetime.now())


def typ_from_id(item_id):
    typ = ''
    try:
        with psycopg2.connect(dsn.postgres_dsn) as pg2:
            c = pg2.cursor()
            c.execute("""SELECT product,version
                FROM public.items as Items
                JOIN public.models as Models
                ON (Items.model_id = Models.Id)
                WHERE Inventory_Code = %s;""", item_id)
            rows = c.fetchone()
            if rows is not None:
                typ = (rows[0] + " " + rows[1]),
    except:
        pass
    return typ


class Sqlite(DB):
    """
    SQLite instance of the DB class
    """

    def __init__(self, filename):
        self.filename = filename
        with sqlite3.connect(filename) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS Leihe
                ( item TEXT
                , name TEXT
                , email TEXT
                , claimed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                , returned_time TIMESTAMP
                );
            ''')
            conn.commit()

            c.execute('''
                CREATE TABLE IF NOT EXISTS Anwesenheit
                (name TEXT
                , email TEXT
                , tag DATE
                 );
            ''')
            conn.commit()

    #
    # Required function implementations
    #

    def claimed(self, item_id):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute("SELECT name, email FROM Leihe WHERE item=? AND returned_time IS NULL ORDER BY claimed_time DESC LIMIT 1", (item_id,))
            return c.fetchone()

    def claimed_by_me(self, item_id, email):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute("SELECT name, email FROM Leihe WHERE item=? AND email=? AND returned_time IS NULL", (item_id,email,))
            return c.fetchone()

    def claimed_by_else(self, item_id, email):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute("SELECT name, email FROM Leihe WHERE item=? AND NOT email=? AND returned_time IS NULL", (item_id,email,))
            return c.fetchone()

    def still_claimed(self, email=None, overall=False):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            if not (overall or (email is None)):
                c.execute("SELECT item FROM Leihe WHERE email=? AND returned_time IS NULL", (email,))
            else:
                c.execute("SELECT item FROM Leihe WHERE returned_time IS NULL")
            items = c.fetchall()

            for i in items:
                items[items.index(i)] = items[items.index(i)] + typ_from_id(i)

        return items

    def item_usage(self, item_id):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute("SELECT name, email, claimed_time, returned_time FROM Leihe WHERE item=? AND claimed_time BETWEEN date('now', '-7 days') AND datetime('now', 'localtime')", (item_id,))
            items = c.fetchall()

        return items

    def hello(self, name, email):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO Anwesenheit VALUES (?, ?, date("now"))', (name, email))
            conn.commit()

            c.execute('SELECT COUNT(DISTINCT email) FROM Anwesenheit WHERE tag=date("now") GROUP BY tag')
            conn.commit()
            da = c.fetchone()

        i = InfluxDBClient(host=dsn.influx_host, port=dsn.influx_port, username=dsn.influx_user, password=dsn.influx_pass)
        i.switch_database(dsn.influx_db)
        json_body = [
            {
                "measurement": "qr_anwesend",
                "fields": {
                    "value": da[0]
                }
            }
        ]
        i.write_points(json_body)

    def claim(self, item_id, name, email):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO Leihe VALUES (?, ?, ?, datetime("now"), NULL)', (item_id, name, email))
            conn.commit()

    def return_time(self, item_id, when):
        # The 'DB' class just enforces type checks
        super.return_time()
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('UPDATE Leihe SET returned_time=? WHERE item=? AND returned_time IS NULL', (when, item_id))
            conn.commit()

    def here_today(self):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('SELECT DISTINCT name, email FROM Anwesenheit WHERE tag=date("now")')
#            c.execute('SELECT DISTINCT name FROM Anwesenheit WHERE tag=date("now")')
            items = c.fetchall()
        return items
    #
    # Optional implementations
    #

    def return_now(self, item_id, email):
        """
        Marks an item as returned

        SQLite provides 'time("now")' so we can use that instead of having to convert Python time
        """
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('UPDATE Leihe SET returned_time=datetime("now") WHERE item=? AND email=? AND returned_time IS NULL',
                      (item_id,email,))
            conn.commit()

