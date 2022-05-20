import sqlite3


class DBManger:
    def __init__(self) -> None:
        self.__conn = sqlite3.connect("clients.db", check_same_thread=False)
        self.__cursor = self.__conn.cursor()
        self.__setup_db()

    def __setup_db(self):
        self.__cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS  users (
            "email"	TEXT,
            "password"	TEXT,
            PRIMARY KEY("email")
        );
        """
        )

    def login(self, email: str, password: str) -> bool:
        check_user = f"SELECT * FROM users WHERE email = '{email}'  and password = '{password}'"
        self.__cursor.execute(check_user)
        ans = self.__cursor.fetchall()

        return len(ans) == 1

    def signup(self, email: str, password: str) -> bool:
        check_user = f"SELECT * FROM users WHERE email = '{email}'"
        self.__cursor.execute(check_user)
        ans = self.__cursor.fetchall()
        if len(ans) == 1:
            return False

        insert = f"INSERT INTO users VALUES ('{email}', '{password}');"
        self.__cursor.execute(insert)
        self.__conn.commit()
        return True
