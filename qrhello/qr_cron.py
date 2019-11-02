#!/usr/bin/python3

import sqlite3
from influxdb import InfluxDBClient

import qrhello.db_dsn as dsn

with sqlite3.connect(self.filename) as conn:
    c = conn.cursor()
    c.execute('INSERT INTO Anwesenheit VALUES (?, ?, date("now"))', (name, email))
    conn.commit()

    c.execute('SELECT COUNT(DISTINCT email) FROM Anwesenheit WHERE tag=date("now") GROUP BY tag')
    conn.commit()
    da = c.fetchone()

with InfluxDBClient(host=dsn.influx_host, port=dsn.influx_port, username=dsn.influx_user,
                    password=dsn.influx_pass) as i:
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
