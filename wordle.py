# Backend-apps for wordle app

import dataclasses
import random
import sqlite3
import textwrap
import json

import databases
import toml

from quart import Quart, g, request, abort, make_response, jsonify
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)


@dataclasses.dataclass
class User:
    username: str
    password: str


async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()


@app.route("/", methods=["GET"])
async def index():
    return textwrap.dedent(
        """
        <h1>Wordle Game</h1>
        <p>To play the game, login or create an account.</p>\n
        """
    )


@app.route("/users", methods=["POST"])
@validate_request(User)
async def create_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)

    try:
        await db.execute(
            """
                INSERT INTO users(username, password) values (:username, :password)
            """,
            user
        )

    except sqlite3.IntegrityError as e:
        abort(409, e)

    return {"Message": "User Successfully Created. Please create a game"}, 201


@app.route("/login", methods=["GET"])
async def login():
    db = await _get_db()

    await check_user(db, request.authorization)

    success_response = {"authenticated": True}
    return success_response, 200


@app.route("/games", methods=["POST"])
async def create_game():
    db = await _get_db()

    user_id = await check_user(db, request.authorization)

    # open a file and load json from it
    answers = load_json_from_file('./share/correct.json')
    print(len(answers))
    print(answers)
    # select a word from list of secret words, word should be different from any word previously assigned to users
    while True:
        length = len(answers)
        chosen_word = answers[random.randint(1, length-1)]
        print('chosen word : ' + chosen_word)
        word_exists = await db.fetch_all('SELECT 1 from games where secret_word = :secret_word'
                                         , values={"secret_word": chosen_word})
        if not word_exists:
            break

    game_id = await db.execute("INSERT INTO games(user_id, secret_word) VALUES(:user, :secret_word)"
                         , values={"user": user_id, "secret_word": chosen_word})

    return {"game_id": game_id, "message": "Game Successfully Created"}, 200


@app.route("/games/<int:game_id>/guesses", methods=["POST"])
async def play_game(game_id):
    db = await _get_db()
    data = await request.json
    if not data:
        abort(400, "Bad Request: Please enter a word")
    word = data["word"]
    if len(word) != 5:
        abort(400, "Bad Request: Word length should be 5")

    user_id = await check_user(db, request.authorization)

    # open a file and load json from it
    answers = load_json_from_file('./share/correct.json')
    valid_words = load_json_from_file('./share/valid.json')
    total_valid_words = answers + valid_words

    if word not in total_valid_words:
        abort(400, "Bad Request: Not a valid guess")

    result = await db.fetch_one("SELECT secret_word FROM games WHERE user_id=:user_id AND game_id=:game_id",
                                values={"game_id": game_id, "user_id": user_id})
    if not result:
        abort(400, "No game with this identifier for your username")
    else:
        return "Working"


async def check_user(db, auth):
    if auth is not None:
        print(auth.type + auth.username + auth.password)

    if auth is not None and auth.type == 'basic':
        result = await db.fetch_one("SELECT user_id FROM users where username = :username and password =:password",
                                         values={"username": auth.username, "password": auth.password})
        print('inside auth')
        app.logger.debug(type(result))
        if result:
            return result.user_id
        else:
            print('inside abort')
            abort(401)
    else:
        abort(401)


def load_json_from_file(file_name):
    f = open(file_name)
    data = json.load(f)
    values = []
    # converting unicode to string
    for item in data:
        values.append(str(item))
    return values


@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400


@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409


@app.errorhandler(401)
def unauthorized(e):
    print(e)
    return {}, 401, {"WWW-Authenticate": "Basic realm='Wordle Site'"}


@app.errorhandler(400)
def bad_request(e):
    return jsonify({'message': e.description}), 400
