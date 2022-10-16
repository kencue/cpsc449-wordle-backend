PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS guesses;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE,
    password VARCHAR NOT NULL
);
-- 0 means game in progress, 1 means game finished
CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    secret_word VARCHAR NOT NULL,
    game_finished INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE guesses(
    guess_id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    valid_word VARCHAR NOT NULL,
    guess_number INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id)
);

COMMIT;
