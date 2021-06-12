import sqlite3


class DB:
    @staticmethod
    def set_up_tables(db):
        db.execute('''CREATE TABLE IF NOT EXISTS corps (id number, name text)''')
        db.execute('''CREATE TABLE IF NOT EXISTS characters (id number, name text)''')
        db.execute(
            '''CREATE TABLE IF NOT EXISTS transfers ''' +
            '''(id text, date text, character number, source number, destination number)'''
        )
        db.execute(
            '''CREATE TABLE IF NOT EXISTS transfers_minus_short_npc ''' +
            '''(id text, date text, character number, source number, destination number)'''
        )

    @staticmethod
    def connect():
        return sqlite3.connect("./WHHistory.sqlite3")
