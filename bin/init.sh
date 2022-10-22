# Create a database wordle.db and exit after creating it
sqlite3 ./var/wordle.db ".exit"
# Create tables to store words
sqlite3 ./var/wordle.db  < ./share/words.sql
# insert values in valid_words and correct_words tables from json files
python3 ./bin/init.py
# create other tables required for storing user information and playing the wordle game
sqlite3 ./var/wordle.db  < ./share/game.sql