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
    secret_word_id INTEGER NOT NULL,
    state INTEGER DEFAULT 0,
    guess_remaining INTEGER DEFAULT 6,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(secret_word_id) REFERENCES correct_words(correct_word_id)
);

CREATE TABLE guesses(
    guess_id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    valid_word_id INTEGER NULL,
    guess_number INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id),
    FOREIGN KEY(valid_word_id) REFERENCES valid_words(valid_word_id)
);



INSERT INTO users(username, password)
values
    ('dummy', 'abc'),
    ('money', 'abc');

INSERT INTO games(user_id, secret_word_id, guess_remaining) VALUES
    (1, 1, 5),
    (1, 2, 5),
    (2, 3, 5),
    (2, 4, 4);

INSERT INTO guesses(game_id, valid_word_id, guess_number) VALUES
    (1, 1, 1),
    (2, 2, 1),
    (3, 3, 1),
    (4, 4, 1),
    (4, 5, 2);

COMMIT;

