import dataclasses
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
    is_win: bool
    number_of_guesses: int


@tag(["Leaderboard"])
@app.route("/leaderboard", methods=["GET"])
async def leaderboard():
    """ Returns the top 10 users based on the average of their scores """
    r = redis.Redis()
    res = r.zrevrange("leaderboard", 0, 9, True)
    return jsonify(res), 200


@tag(["Leaderboard"])
@app.route("/add-leaderboard-entry", methods=["POST"])
@validate_request(Entry)
async def add_entry(data):
    """
    Reports game results by entry, recalculates the user's average, then 
    updates the leaderboard average score.
    We are storing entries as user: { game1: score1, game2: score2, ... }."""
    r = redis.Redis()

    # add the game result
    entry = dataclasses.asdict(data)
    score = calculate_score(entry["is_win"], entry["number_of_guesses"])
    r.hset("user:" + entry["username"], "game:" + entry["game_id"], score)

    # get all the games of the user so we can calculate the average
    games = r.hgetall("user:" + entry["username"])

    mean = 0
    for val in games.values():
        mean += int(val)
    
    mean = mean / len(games)

    # update the leaderboard with the mean
    leaderboard_entry = {
        "user:" + entry["username"] : mean
    }
    r.zadd("leaderboard", leaderboard_entry)
    return "OK", 200


def calculate_score(is_win, number_of_guesses):
    max_guesses = 6
    win_bonus = 0
    if is_win:
        win_bonus = 1
    score = win_bonus * ((max_guesses - number_of_guesses) + win_bonus)
    return score


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