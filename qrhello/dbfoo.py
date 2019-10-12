import time
import datetime
import sqlite3
import psycopg2


class DB:
    #
    # Required functions to implement
    #

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
                , claimed_time TIMESTAMP
                , returned_time TIMESTAMP
                )
            ''')
            conn.commit()

    #
    # Required function implementations
    #

    def claimed(self, item_id):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute("SELECT name, email FROM Leihe WHERE item=? AND returned_time IS NULL", (item_id,))
            return c.fetchone()


    def still_claimed(self, email):
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute("SELECT item FROM Leihe WHERE email=? AND returned_time IS NULL", (email,))
            items = c.fetchall()

        try:
            with psycopg2.connect(
            "dbname='leihs' user='leihs_reader' host='141.64.71.42' password='<PASSWORD>'") as pg2:
                c=pg2.cursor()
                for i in items:
                    c.execute("""SELECT product,version 
                        FROM public.items as Items 
                        JOIN public.models as Models 
                        ON (Items.model_id = Models.Id) 
                        WHERE Inventory_Code = %s;""", i)
                    rows = c.fetchone()
                    if rows != None:
                        type = (rows[0] + " " + rows[1]),
                        items[items.index(i)] = items[items.index(i)] + type
        except:
            pass
        return items


    def claim(self, item_id, name, email):
        self.return_now(item_id)
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO Leihe VALUES (?, ?, ?, time("now"), NULL)', (item_id, name, email))
            conn.commit()


    def return_time(self, item_id, when):
        # The 'DB' class just enforces type checks
        super.return_time()
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('UPDATE Leihe SET returned_time=? WHERE item=? AND returned_time IS NULL', (when, item_id))
            conn.commit()


    #
    # Optional implementations
    #

    def return_now(self, item_id):
        """
        Marks an item as returned

        SQLite provides 'time("now")' so we can use that instead of having to convert Python time
        """
        with sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('UPDATE Leihe SET returned_time=time("now") WHERE item=? AND returned_time IS NULL', (item_id,))
            conn.commit()
