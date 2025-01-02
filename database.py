import sqlite3


class DataBase:
    """
    Wrapper class to store a database object and simplify queries
    """

    def __init__(self, database):
        self.con = sqlite3.connect(database, check_same_thread=False)
        # Add header names to responses
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

    def insert(self, query, *args):
        """
        Inserts rows into the database

        PARAMETERS :-
            query: SQL query that needs to be executed
            *args: Positional arguments that need to be replaced in the query

        RETURNS :-
            None
        """

        self.cur.execute(query, args)
        self.con.commit()

    # All these work same as insert, alias to make code more readable
    update = insert
    delete = insert
    create = insert

    def select(self, query, *args):
        """
        Selects rows from the database

        PARAMETERS :-
            query: SQL query that needs to be executed
            *args: Positional arguments that need to be replaced in the query

        RETURNS :-
            The result of the SQL Select query
        """

        res = self.cur.execute(query, args)
        return res.fetchall()
