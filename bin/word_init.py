# Imports
import json
import sqlite3


def populate_words(cur: sqlite3.Cursor):

    # Make sure tables are empty first
    cur.execute("DELETE from correct_words")
    cur.execute("DELETE from valid_words")

    with open("./share/correct.json") as file:
        correctWordList = json.load(file)

    with open("./share/valid.json") as file:
        validWordList = json.load(file)


    correctWordList = [(word,) for word in correctWordList]
    validWordList = [(word,) for word in validWordList]

    # Simple fix for not allowing correct words to be guessed
    validWordList.extend(correctWordList)

    cur.executemany("INSERT INTO correct_words(correct_word) values(?)", correctWordList)
    cur.executemany("INSERT INTO valid_words(valid_word) values(?)", validWordList)
    
    return len(correctWordList) + len(validWordList)




if __name__ == "__main__":
    connection = sqlite3.connect("./var/primary/mount/game.db")
    cursor = connection.cursor()


    count = populate_words(cursor)
    connection.commit()
    print(f"Successfully inserted {count} words")
