import sqlite3
from datetime import datetime


class DbWorker:
    def __init__(self):
        self.conn = sqlite3.connect("tin.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

    def get_true_users(self):
        self.cursor.execute("select * from tinkoff_true_user")
        records = self.cursor.fetchall()
        true_user = set([int(x[0]) for x in records])
        return true_user

    def add_user(self, user_id):
        try:
            self.cursor.execute("insert into tinkoff_true_user values('{0}')".format(user_id))
            self.conn.commit()
        except Exception:
            print(Exception)

    def top_up(self, user_id, sum):
        try:
            self.cursor.execute("insert into tinkoff_true_user values('{0}', '{1}')".format(user_id, sum))
            self.conn.commit()
        except Exception:
            print(Exception)

    def buy_stocks(self, user_id, ticker, price, cnt):
        try:
            self.cursor.execute("insert into buy_history values(?, ?, ?, ?, ?)",
                                (ticker, str(price), cnt, datetime.now(), user_id))
            self.conn.commit()
        except Exception as e:
            print(e)

    def get_stocks(self, user_id):
        self.cursor.execute("select * from buy_history where user_id = '{0}'".format(user_id))
        records = self.cursor.fetchall()
        return records
