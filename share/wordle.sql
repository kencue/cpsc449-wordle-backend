PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS guesses;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE,
    password VARCHAR NOT NULL
);
-- state - 0 means game in progress, 1 means game finished and won the game, 2 means finished and lost the game
CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    secret_word VARCHAR NOT NULL,
    state INTEGER DEFAULT 0,
    guess_remaining INTEGER DEFAULT 6,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE guesses(
    guess_id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    valid_word VARCHAR NOT NULL,
    guess_number INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id)
);

INSERT INTO users(username, password)
values
    ('dummy', 'abc'),
    ('money', 'abc');

INSERT INTO games(user_id, secret_word, guess_remaining) VALUES
    (1, 'munch', 5),
    (1, 'water', 5),
    (2, 'rebut', 5),
    (2, 'blush', 4);

INSERT INTO guesses(game_id, valid_word, guess_number) VALUES
    (1, 'water', 1),
    (2, 'cater', 1),
    (3, 'flask', 1),
    (4, 'anker', 1),
    (4, 'paste', 2);

COMMIT;
