import sqlite3
import requests
import json
import datetime
import Transfer


def split(array, n):
    return [array[i * n:(i + 1) * n] for i in range((len(array) + n - 1) // n)]


class DB:
    @staticmethod
    def set_up_tables(db):
        db.execute('''CREATE TABLE IF NOT EXISTS corps (id number, name text)''')
        db.execute('''CREATE TABLE IF NOT EXISTS characters (id number, name text)''')
        db.execute(
            '''CREATE TABLE IF NOT EXISTS transfers ''' +
            '''(id text, date text, character number, source number, destination number)'''
        )

    @staticmethod
    def connect():
        return sqlite3.connect("./WHHistory.sqlite3")

    @staticmethod
    def populate_corps():
        db = DB.connect()
        source_corp_list = list(map(lambda r: r[0], db.execute("SELECT source FROM transfers").fetchall()))
        destination_corp_list = list(map(lambda r: r[0], db.execute("SELECT destination FROM transfers").fetchall()))
        corp_list = list(set(source_corp_list + destination_corp_list))
        for sublist in split(corp_list, 100):
            resp = requests.post(
                "https://esi.evetech.net/latest/universe/names/?datasource=tranquility&language=en",
                data=json.dumps(sublist),
                headers={'Accept': 'application/json', 'Accept-Language': 'en', 'Content-Type': 'application/json'}
            ).json()
            for corp in resp:
                print(corp)
                db.execute("INSERT INTO corps VALUES (?, ?)", (corp["id"], corp["name"]))
            db.commit()

    @staticmethod
    def get_transfers_into_corp(db, corp_id):
        raw = db.execute("SELECT * FROM transfers WHERE destination=? ORDER BY date ASC", (corp_id,)).fetchall()
        return list(map(lambda t: Transfer.Transfer(t[0], t[1], t[2], t[3], t[4]), raw))

    @staticmethod
    def get_transfers_out_of_corp(db, corp_id):
        raw = db.execute("SELECT * FROM transfers WHERE source=? ORDER BY date ASC", (corp_id,)).fetchall()
        return list(map(lambda t: Transfer.Transfer(t[0], t[1], t[2], t[3], t[4]), raw))

    @staticmethod
    def get_corp_starting_date(db, corp_id):
        start_date_string = db.execute("SELECT MIN(date) FROM transfers WHERE destination=?", (corp_id,)).fetchall()[0][0]
        return datetime.datetime.fromisoformat(start_date_string.replace("T", " ").replace("Z", ""))

    @staticmethod
    def get_corp_dict(db):
        corps = db.execute("SELECT * FROM corps")
        output = {}
        for line in corps:
            output[line[0]] = line[1]
        return output
