# Imports
import sqlite3
import random
import uuid
import hashlib
import base64
import secrets

ALGORITHM = "pbkdf2_sha256"


# Hash a given password using pbkdf2.
def hash_password(password, salt=None, iterations=260000):
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iterations, salt, b64_hash)


# insert into query for games and guesses table
def insert_into_games(cur: sqlite3.Cursor, username: str):

    res = cur.execute(
        """
        SELECT count(*) count 
        FROM correct_words
        """
    ).fetchone()
    length = res[0]

    uuid1 = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO games(game_id, username, secret_word_id, guess_remaining)
        VALUES(:uuid, :username, :secret_word_id, :guesses)
        """,
        {
            "uuid": uuid1,
            "username": username,
            "secret_word_id": random.randint(1, length),
            "guesses": 5 # Set to 5 since we add random guess next
        },
    )

    res = cur.execute(
        """
        SELECT count(*) count
        FROM valid_words
        """
    ).fetchone()
    length = res[0]

    cur.execute(
        """
        INSERT INTO guesses(game_id, valid_word_id, guess_number)
        VALUES(:game_id, :valid_word_id, :guess_number)
        """,
        {
            "game_id": uuid1,
            "valid_word_id": random.randint(1, length),
            "guess_number": 1,
        },
    )


# insert into queries user table
def insert_into_users(cur: sqlite3.Cursor, user: dict):

    cur.execute(
        """
        INSERT INTO users(username, password) values (:username, :password)
        """,
        user,
    )



# Run when executed as script.
if __name__ == "__main__":
    user_con = sqlite3.connect("./var/user.db")

    user_cur = user_con.cursor()

    # Clean slate
    user_cur.execute("DELETE FROM users")

    user1 = {"username": "dummy", "password": hash_password("abc")}
    user2 = {"username": "money", "password": hash_password("abc")}

    print("Loading data into users table")
    insert_into_users(user_cur, user1)
    insert_into_users(user_cur, user2)
    user_con.commit()
    user_con.close()

    game_con = sqlite3.connect("./var/primary/mount/game.db")
    game_cur = game_con.cursor()

    game_cur.execute("DELETE FROM guesses")
    game_cur.execute("DELETE FROM games")

    print("Loading data into games table")
    insert_into_games(game_cur, user1["username"])
    insert_into_games(game_cur, user1["username"])
    insert_into_games(game_cur, user2["username"])
    insert_into_games(game_cur, user2["username"])

    game_con.commit()
    game_con.close()

    print("Loading of tables complete")
