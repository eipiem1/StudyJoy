def create_tables(db):
    """
    Creates tables in the database if they don't exist

    PARAMETERS :-
        db: Database connection object

    RETURNS :-
        None
    """

    db.create(
        """CREATE TABLE IF NOT EXISTS users 
              (user_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
              username TEXT NOT NULL, 
              password TEXT NOT NULL)
              ;"""
    )

    db.create(
        """CREATE TABLE IF NOT EXISTS flashcards2 
              (word TEXT PRIMARY KEY NOT NULL, 
              translation TEXT NOT NULL, 
              root_explanation TEXT NOT NULL, 
              memory_story TEXT NOT NULL, 
              example_sentence TEXT NOT NULL, 
              image_url TEXT NOT NULL)
              ;"""
    )

def init(db):
    """
    Driver function to initialize the database

    PARAMETERS :-
        db: Database connection object

    RETURNS :-
        None
    """

    create_tables(db)
