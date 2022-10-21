sqlite3 ./var/wordle.db ".exit"
sqlite3 ./var/wordle.db  < ./share/wordle1.sql
python3 ./bin/init.py
sqlite3 ./var/wordle.db  < ./share/wordle.sql