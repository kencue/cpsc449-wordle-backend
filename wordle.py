#!/usr/bin/env python3.8
# Imports
import dataclasses
import random
import sqlite3
import textwrap
import databases
from sqlalchemy import true
import toml
import base64
import hashlib
import secrets
from quart import Quart, g, request, abort, jsonify
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request, tag

# Encryption type.
ALGORITHM = "pbkdf2_sha256"

# Initialize the app
app = Quart(__name__)
QuartSchema(app, tags=[{"name": "Users", "description": "APIs for creating a user and authenticating a user"},
                       {"name": "Games", "description": "APIs for creating a game and playing a game for a particular "
                                                        "user"},
                       {"name": "Statistics", "description": "APIs for checking user statistics"},
                       {"name": "Root", "description": "Root path returning html"}])
app.config.from_file(f"./etc/{__name__}.toml", toml.load)

# Decorator to examine class and find fields
@dataclasses.dataclass
class User:
    username: str
    password: str


@dataclasses.dataclass
class Word:
    guess: str

# Establish database connection
async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db

# Terminate database connection
@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@tag(["Root"])
@app.route("/", methods=["GET"])
async def index():
    """ Root path, returns HTML """
    return textwrap.dedent(
        """
        <h1>Wordle Game</h1>
        <p>To play the game, login or create an account.</p>\n
        """
    )

@tag(["Users"])
@app.route("/users", methods=["POST"])
@validate_request(User)
async def create_user(data):
    """  Create a user """
    db = await _get_db()
    user = dataclasses.asdict(data)
    # Encrypt password
    user["password"] = hash_password(user["password"])
    # Insert into database
    try:
        await db.execute(
            """
                INSERT INTO users(username, password) values (:username, :password)
            """,
            user
        )
    # Error
    except sqlite3.IntegrityError as e:
        abort(409, e)
    return {"Message": "User Successfully Created. Please login and create a game"}, 201

@tag(["Users"])
# Endpoint for /login, verifies credentials.
@app.route("/login", methods=["GET"])
async def login():
    """ Authenticate the user """
    db = await _get_db()
    await check_user(db, request.authorization)
    success_response = {"authenticated": True}
    return success_response, 200

@tag(["Games"])
@app.route("/users/<string:username>/games", methods=["POST"])
async def create_game(username):
    """ Create a game """
    db = await _get_db()
    user_id = await get_user_id(db, username)

    # Open a file and load json from it
    res = await db.fetch_one("SELECT count(*) count from correct_words")
    # Select a word from list of secret words, word should be different from any word previously assigned to users
    length = res.count
    game_id = await db.execute("INSERT INTO games(user_id, secret_word_id) VALUES(:user, :secret_word_id)"
                               , values={"user": user_id, "secret_word_id": random.randint(1, length)})

    return {"game_id": game_id, "message": "Game Successfully Created"}, 200

@validate_request(Word)
@tag(["Games"])
@app.route("/users/<string:username>/games/<int:game_id>", methods=["POST"])
async def play_game(username, game_id):
    """ Play the game (creating a guess) """
    data = await request.json
    db = await _get_db()
    user_id = await get_user_id(db, username)

    return await play_game_or_check_progress(db, user_id, game_id, data["guess"])

@tag(["Games"])
@app.route("/users/<string:username>/games/<int:game_id>", methods=["GET"])
async def check_game_progress(username, game_id):
    """ Check the state of a game that is in progress. If game is over show whether user won/lost and no. of guesses """
    db = await _get_db()
    user_id = await get_user_id(db, username)

    return await play_game_or_check_progress(db, user_id, game_id)

@tag(["Statistics"])
@app.route("/users/<string:username>/games", methods=["GET"])
async def get_in_progress_games(username):
    """ Check the list of in-progress games for a particular user """
    db = await _get_db()
    user_id = await get_user_id(db, username)

    # showing only in-progress games
    games_output = await db.fetch_all("SELECT guess_remaining,game_id, state FROM games where user_id =:user_id "
                                      "and state = :state ", values={"user_id": user_id, "state": 0})

    in_progress_games = []
    for guess_remaining, game_id, state in games_output:
        in_progress_games.append({
            "guess_remaining": guess_remaining,
            "game_id": game_id
        })

    return in_progress_games

@tag(["Statistics"])
@app.route("/users/<string:username>/statistics", methods=["GET"])
async def statistics(username):
    """ Checking the statistics for a particular user """
    db = await _get_db()
    user_id = await get_user_id(db, username)

    res_games = await db.fetch_all("SELECT state, count(*) from games where user_id=:user_id GROUP BY state",
                                   values={"user_id": user_id})
    states = {0: 'In Progress', 1: 'Win', 2: "Loss"}
    games_stats = {}
    for state, count in res_games:
        games_stats[states[state]] = count

    return games_stats

# Error status: Client error.
@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400

# Error status: Cannot process request.
@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409

# Error status: Unauthorized client.
@app.errorhandler(401)
def unauthorized(e):
    return {}, 401, {"WWW-Authenticate": "Basic realm='Wordle Site'"}

# Error status: Cannot or will not process the request.
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'message': e.description}), 400

async def play_game_or_check_progress(db, user_id, game_id, guess=None):
    states = {0: 'In Progress', 1: 'Win', 2: "Loss"}
    games_output = await db.fetch_one("SELECT correct_words.correct_word secret_word, guess_remaining, state "
                                      "FROM games join correct_words WHERE user_id=:user_id "
                                      "AND game_id=:game_id AND correct_words.correct_word_id=games.secret_word_id",
                                      values={"game_id": game_id, "user_id": user_id})

    if not games_output:
        abort(400, "No game with this identifier for your username")

    if games_output["state"] != 0:
        return {"number_of_guesses": 6 - games_output["guess_remaining"],
                "decision": states.get(games_output["state"])}, 200

    secret_word = games_output["secret_word"]
    state = 0
    guess_remaining = games_output["guess_remaining"]

    if guess:
        if len(guess) != 5:
            abort(400, "Bad Request: Word length should be 5")
        # when the user guessed the correct word
        if guess == secret_word:
            state = 1

        valid_word_output = await db.fetch_one("SELECT valid_word_id from valid_words WHERE valid_word =:word",
                                               values={"word": guess})
        if not valid_word_output:
            if not state:
                abort(400, "Bad Request: Not a valid guess")

        # Decrement the guess remaining
        guess_remaining = guess_remaining - 1

        # Game is over, update the game
        if guess_remaining == 0 or state:
            # user lost the game
            if guess_remaining == 0 and state == 0:
                state = 2
            await db.execute("UPDATE games set guess_remaining=:guess_remaining,state=:state  "
                             "where game_id=:game_id",
                             values={"guess_remaining": guess_remaining, "game_id": game_id, "state": state})
            return {"game_id": game_id, "number_of_guesses": 6 - guess_remaining, "decision": states[state]}, 200
        else:
            await db.execute("UPDATE games set guess_remaining=:guess_remaining where game_id=:game_id",
                             values={"guess_remaining": guess_remaining, "game_id": game_id})

            guess_number = 6 - guess_remaining
            valid_word_id = valid_word_output.valid_word_id
            await db.execute('INSERT INTO guesses(game_id, valid_word_id, guess_number) '
                             'VALUES(:game_id, :valid_word_id, :guess_number)'
                             ,
                             values={"game_id": game_id, "valid_word_id": valid_word_id, "guess_number": guess_number})
    # Prepare the response
    guess_output = await db.fetch_all("SELECT guess_number, valid_words.valid_word from guesses join "
                                      "valid_words where game_id=:game_id "
                                      "and valid_words.valid_word_id=guesses.valid_word_id "
                                      " order by guess_number",
                                      values={"game_id": game_id})
    guesses = []
    for guess_number, valid_word in guess_output:
        correct_positions, incorrect_positions = compare(secret_word, valid_word)
        guesses.append(
            {
                "guess": valid_word,
                "guess_number": guess_number,
                "correct_positions": dict(correct_positions),
                "incorrect_positions:": dict(incorrect_positions),
            }
        )

    return {"guesses": guesses, "guess_remaining": guess_remaining, "game_state": states[state]}, 200

async def get_user_id(db, username):
    res = await db.fetch_one("SELECT user_id from users where username=:user_name ",
                             values={"user_name": username})
    if not res:
        abort(401)
    return res.user_id

# Function to compare the guess to answer.
def compare(secret_word, guess):
    secret_word_lst = [i for i in enumerate(secret_word)]
    guess_list = [i for i in enumerate(guess)]

    temp_correct_positions = []
    correct_positions = []
    incorrect_positions = []
    for i in range(0, len(secret_word)):
        if guess_list[i][1] == secret_word_lst[i][1]:
            temp_correct_positions.append(guess_list[i])
            correct_positions.append(((guess_list[i][0] + 1), guess_list[i][1]))

    secret_word_lst = [i for i in secret_word_lst if i not in temp_correct_positions]
    guess_list = [i for i in guess_list if i not in temp_correct_positions]

    for i in range(len(guess_list)):
        for j in range(len(secret_word_lst)):
            # found a character which is in a different position
            if guess_list[i][1] == secret_word_lst[j][1]:
                incorrect_positions.append((guess_list[i][0] + 1, guess_list[i][1]))
                secret_word_lst.pop(j)
                break

    return correct_positions, incorrect_positions

# User authentication.
async def check_user(db, auth):

    if auth is not None and auth.type == 'basic':
        user_info = await db.fetch_one("SELECT password FROM users where username = :username",
                                       values={"username": auth.username})
        if user_info:
            if verify_password(auth.password, user_info["password"]):
                return True
            else:
                abort(401)
        else:
            abort(401)
    else:
        abort(401)

# Hash a given password using pbkdf2.
def hash_password(password, salt=None, iterations=260000):
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iterations, salt, b64_hash)

# Verify a password by comparing it to the hash.
def verify_password(password, password_hash):
    if (password_hash or "").count("$") != 3:
        abort(401)
    algorithm, iterations, salt, b64_hash = password_hash.split("$", 3)
    iterations = int(iterations)
    assert algorithm == ALGORITHM
    compare_hash = hash_password(password, salt, iterations)
    return secrets.compare_digest(password_hash, compare_hash)
