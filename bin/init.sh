# Create a database user.db and exit after creating it
sqlite3 ./var/user.db  < ./share/users.sql

# Create tables to store words
sqlite3 ./var/game.db ".exit"
sqlite3 ./var/game.db  < ./share/words.sql

# insert values in valid_words and correct_words tables from json files
python3 ./bin/word_init.py

# create other tables required for storing user information and playing the wordle game
sqlite3 ./var/game.db  < ./share/game.sql

# populate the user and games table with dummy values
python3 ./bin/game_init.py