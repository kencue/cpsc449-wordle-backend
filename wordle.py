# Imports
import dataclasses
import random
import sqlite3
import textwrap
import json
import databases
import toml
from quart import Quart, g, request, abort, jsonify
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

# Initialize the app
app = Quart(__name__)
QuartSchema(app)
app.config.from_file(f"./etc/{__name__}.toml", toml.load)

# Decorator to examine class and find fields
@dataclasses.dataclass
class User:
    username: str
    password: str

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
       
# Endpoint for root path, returns HTML.
@app.route("/", methods=["GET"])
async def index():
    return textwrap.dedent(
        """
        <h1>Wordle Game</h1>
        <p>To play the game, login or create an account.</p>\n
        """
    )

# Endpoint for /users, posts user data (username and password)
@app.route("/users", methods=["POST"])
@validate_request(User)
async def create_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)
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
    return {"Message": "User Successfully Created. Please create a game"}, 201

# Endpoint for /login, verifes credentials.
@app.route("/login", methods=["GET"])
async def login():
    db = await _get_db()
    user_id = await check_user(db, request.authorization)
    await db.execute("UPDATE users set is_authenticated = 1 where user_id=:user_id", values={"user_id": user_id})
    success_response = {"authenticated": True}
    return success_response, 200

# Endpoint for /games, creates a game for verified user.
@app.route("/games", methods=["POST"])
async def create_game():
    db = await _get_db()
    data = await request.json
    res = await db.fetch_one("SELECT user_id from users where username=:user_name "
                             "and is_authenticated =:is_authenticated",
                             values={"user_name": data['username'], "is_authenticated": 1})
    if not res:
        abort(401)
    print(res.user_id)
    user_id = res.user_id
    # Open a file and load json from it
    res = await db.fetch_one("SELECT count(*) count from correct_words")
    # Select a word from list of secret words, word should be different from any word previously assigned to users
    length = res.count
    print(length)
    game_id = await db.execute("INSERT INTO games(user_id, secret_word_id) VALUES(:user, :secret_word_id)"
                               , values={"user": user_id, "secret_word_id": random.randint(1, length - 1)})

    return {"game_id": game_id, "message": "Game Successfully Created"}, 200

# Endpoint for /stats, data regarding user statistics
@app.route("/stats",methods=["POST"])
async def statistics():
    db = await _get_db()
    data = await request.json
    res = await db.fetch_one("SELECT user_id from users where username=:user_name "
                             "and is_authenticated =:is_authenticated",
                             values={"user_name": data['username'], "is_authenticated": 1})
    if not res:
        abort(401)
    print(res.user_id)
    user_id = res.user_id

    res_games = await db.fetch_all("SELECT guess_remaining,game_id FROM games where user_id =:user_id ",
                                   values={"user_id" : user_id})

    print(res_games)
    games_stats = []
    for guess_remaining,game_id in res_games:
        games_stats.append({
            "guess_remaining":guess_remaining,
            "game_id":game_id
        })

    return games_stats

# Endpoint for /results, additional statistics.
@app.route("/results",methods=["POST"])
async def result():
    db = await _get_db()
    data = await request.json
    res = await db.fetch_one("SELECT user_id from users where username=:user_name "
                             "and is_authenticated =:is_authenticated",
                             values={"user_name": data['username'], "is_authenticated": 1})
    if not res:
        abort(401)
    print(res.user_id)
    user_id = res.user_id

    res_games = await db.fetch_all("SELECT state, count(*) from games where user_id=:user_id GROUP BY state",
                                   values={"user_id" : user_id})
    states = {0: 'In Progress', 1: 'Win', 2: "Loss"}
    print(res_games)
    games_stats = []
    for state,count in res_games:
        games_stats.append({
            "state":states[state],
            "count":count
        })

    return games_stats

# Endpoint /games/<int:game_id>/play, Core game logic.
@app.route("/games/<int:game_id>/play", methods=["POST"])
async def play_game(game_id):
    db = await _get_db()
    data = await request.json

    data = await request.json
    res = await db.fetch_one("SELECT user_id from users where username=:user_name "
                             "and is_authenticated =:is_authenticated",
                             values={"user_name": data['username'], "is_authenticated": 1})
    if not res:
        abort(401)
    print(res.user_id)
    user_id = res.user_id

    if data is not None and "word" in data:
        guess = data["word"]
        if len(guess) != 5:
            abort(400, "Bad Request: Word length should be 5")
        # Open a file and load json from it
        res0 = await db.fetch_one("SELECT correct_word_id from correct_words WHERE correct_word =:word", values={"word":guess})
        res = await db.fetch_one("SELECT valid_word_id from valid_words WHERE valid_word =:word", values={"word":guess})
        if not res:
            if not res0:
                abort(400, "Bad Request: Not a valid guess")

    states = {0: 'In Progress', 1: 'Win', 2: "Loss"}
    result = await db.fetch_one("SELECT correct_words.correct_word secret_word, guess_remaining, state FROM games "
                                " join correct_words WHERE user_id=:user_id "
                                "AND game_id=:game_id AND correct_words.correct_word_id=games.secret_word_id",
                                values={"game_id": game_id, "user_id": user_id})

    print(result)
    if not result:
        abort(400, "No game with this identifier for your username")
    elif result["state"] != 0:
        return {"number_of_guesses": 6-result["guess_remaining"], "decision": states.get(result["state"])}, 200

    secret_word = result["secret_word"]
    state = 0
    guess_remaining = result["guess_remaining"]
    if data is not None and "word" in data:

        # Decrement the guess remaining
        guess_remaining = guess_remaining - 1

        if guess == secret_word:
            print("Won the game")
            state = 1

        # Game is over, update the game
        if guess_remaining == 0 or state:
            if guess_remaining == 0 and state == 0:
                state = 2
            await db.execute("UPDATE games set guess_remaining=:guess_remaining,state=:state  "
                             "where game_id=:game_id",
                             values={"guess_remaining": guess_remaining, "game_id": game_id, "state": state})
            return {"game_id": game_id, "number_of_guesses": guess_remaining, "decision": states[state]}, 200
        else:
            await db.execute("UPDATE games set guess_remaining=:guess_remaining where game_id=:game_id",
                             values={"guess_remaining": guess_remaining, "game_id": game_id})

            guess_number = 6 - guess_remaining
            valid_word_id = res.valid_word_id
            await db.execute('INSERT INTO guesses(game_id, valid_word_id, guess_number) '
                             'VALUES(:game_id, :valid_word_id, :guess_number)'
                             , values={"game_id": game_id, "valid_word_id": valid_word_id, "guess_number": guess_number})
    # Prepare the response
    res = await db.fetch_all("SELECT guess_number, valid_words.valid_word from guesses join "
                             "valid_words where game_id=:game_id "
                             "and valid_words.valid_word_id=guesses.valid_word_id "
                             " order by guess_number",
                             values={"game_id": game_id})
    guesses = []
    print(res)
    for guess_number, valid_word in res:
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

# Function to compare the guess to answer.
def compare(secret_word, guess):
    secret_word_lst = [i for i in enumerate(secret_word)]
    guess_list = [i for i in enumerate(guess)]
    print("Secret word: {}".format(secret_word_lst))
    print(f"guess: {guess_list}")

    temp_correct_positions = []
    correct_positions = []
    incorrect_positions = []
    for i in range(0, len(secret_word)):
        if guess_list[i][1] == secret_word_lst[i][1]:
            temp_correct_positions.append(guess_list[i])
            correct_positions.append(((guess_list[i][0] + 1), guess_list[i][1]))
    print('Correct positions: ')
    print(temp_correct_positions)
    print(f"Correct index positions are: {correct_positions}")
    print('List after removing correct ones')

    secret_word_lst = [i for i in secret_word_lst if i not in temp_correct_positions]
    print(secret_word_lst)
    guess_list = [i for i in guess_list if i not in temp_correct_positions]
    print(guess_list)

    for i in range(len(guess_list)):
        for j in range(len(secret_word_lst)):
            # found a character which is in a different position
            if guess_list[i][1] == secret_word_lst[j][1]:
                incorrect_positions.append((guess_list[i][0] + 1, guess_list[i][1]))
                secret_word_lst.pop(j)
                break

    print('Incorrect position')
    print(incorrect_positions)

    return correct_positions, incorrect_positions

# User authentication.
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

# Load file and convert unicode to string.
def load_json_from_file(file_name):
    f = open(file_name)
    data = json.load(f)
    values = []
    for item in data:
        values.append(str(item))
    return values

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
    print(e)
    return {}, 401, {"WWW-Authenticate": "Basic realm='Wordle Site'"}

# Error status: Cannot or will not process the request.
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'message': e.description}), 400
