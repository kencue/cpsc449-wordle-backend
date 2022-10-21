# Imports
import json
import asyncio
import databases
import toml
from quart import Quart
from quart_schema import QuartSchema

# Initialize app
app = Quart(__name__)
QuartSchema(app)
app.config.from_file(f"../etc/wordle.toml", toml.load)

# Load json from file and convert unicode to string.
def load_json_from_file(file_name):
    f = open(file_name)
    data = json.load(f)
    values = []
    for item in data:
        values.append(str(item))
    return values

# Establish database connection.
async def _get_db():
    db = databases.Database(app.config["DATABASES"]["URL"])
    await db.connect()
    return db

# Populate valid words into database.
async def valid_words(filename, tablename):
    answers = load_json_from_file(filename)
    print(type(answers))
    res = {}
    for value in answers:
        db = await _get_db()
        res = await db.execute("INSERT into " + tablename + "(" + tablename[:-1] + ") values(:valid_word)",
                               {"valid_word": value})
    return res

# Run when executed as script.
if __name__ == "__main__":
    asyncio.run(valid_words('./share/correct.json', 'correct_words'))
    asyncio.run(valid_words('./share/valid.json', 'valid_words'))
