import sqlite3

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
