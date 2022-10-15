# Backend-apps for wordle app

import dataclasses
import sqlite3
import textwrap

import databases
import toml

from quart import Quart, g, request, abort, make_response
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
                INSERT INTO user(username, password) values (:username, :password)
            """,
            user
        )

    except sqlite3.IntegrityError as e:
        abort(409, e)

    return {"Message": "User Successfully Created. Please create a game"}, 201


@app.route("/login", methods=["GET"])
async def login():
    db = await _get_db()

    auth = request.authorization
    if auth is not None:
        print(auth.type + auth.username + auth.password)

    if auth is not None and auth.type == 'basic':
        user_exists = await db.fetch_one("SELECT 1 from user where username = :username and password =:password",
                                         values={"username": auth.username, "password": auth.password})
        if user_exists:
            success_response = {"authenticated": True}
            return success_response, 200
        else:
            abort(401)
    else:
        abort(401)


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
