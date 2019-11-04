#!/var/lib/qrhello/venv/bin/python3

import sqlite3
from influxdb import InfluxDBClient

import db_dsn as dsn

conn = sqlite3.connect(dsn.sqlite_file)
c = conn.cursor()
c.execute('SELECT COUNT(DISTINCT email) FROM Anwesenheit WHERE tag=date("now") GROUP BY tag')
conn.commit()
da = c.fetchone()

i = InfluxDBClient(host=dsn.influx_host, port=dsn.influx_port, username=dsn.influx_user,
                    password=dsn.influx_pass)
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
