import dataclasses
import databases
import textwrap
import toml
import redis
from quart import Quart, g, request, abort, jsonify
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request, tag


# Initialize the app
app = Quart(__name__)
QuartSchema(app, tags=[{"name": "Leaderboard", "description": "Leaderboard for Wordle Scores"}])
app.config.from_file(f"./etc/wordle.toml", toml.load)

@dataclasses.dataclass
class Entry:
    game_id: str
    username: str
    score: int


@tag(["Leaderboard"])
@app.route("/leaderboard", methods=["GET"])
async def leaderboard():
    """ Returns the top 10 scores """
    return textwrap.dedent(
        """
        TOP 10
        """
    )


@tag(["Leaderboard"])
@app.route("/leaderboard/add", methods=["POST"])
@validate_request(Entry)
async def add_entry(data):
    entry = dataclasses.asdict(data)
    hash_id = "game_id" + entry["game_id"]
    entry = {"username" + entry["username"], "score" + entry["socre"]}

    return entry, 200


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