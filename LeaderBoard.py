import dataclasses
import databases
import textwrap
import toml
import redis
from quart import Quart, g, request, abort, jsonify
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request, tag

# Encryption type.
ALGORITHM = "pbkdf2_sha256"

# Initialize the app
app = Quart(__name__)
QuartSchema(app, tags=[{"name": "LeaderBoard", "description": "LeaderBoard for User Scores"}
                       {"name": "Root", "description": "Root path returning html"}])
app.config.from_file(f"./etc/wordle.toml", toml.load)

@dataclasses.dataclass
class wordle:
    game_id: str
    username: str
    state: str
    score: int

@tag(["Root"])
@app.route("/", methods=["GET"])
async def index():
    """ Root path, returns HTML """
    return textwrap.dedent(
        """
        <h1>Wordle Game</h1>
        <p>To play wordle, go to the <a href="http://tuffix-vm/docs">Games Docs</a></p>\n
        """
    )

@app.route("/LeaderBoard", methods=["POST"])
@tag(["Leaderboard"])
@validate_request(wordle)
async def Game_in_progress(data):
    wordle = dataclasses.asdict(data)
    hash_id = "game_id" + wordle["game_id"]
    wordle_data = {"username" + wordle["username"], "state" + wordle["state"], "score" + wordle["socre"]}




    return wordle, 200