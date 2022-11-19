PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS guesses;
DROP TABLE IF EXISTS games;

-- state - 0 means game in progress, 1 means game finished and won the game, 2 means finished and lost the game
CREATE TABLE games (
    game_id VARCHAR PRIMARY KEY,
    username VARCHAR NOT NULL,
    secret_word_id INTEGER NOT NULL,
    state INTEGER DEFAULT 0,
    guess_remaining INTEGER DEFAULT 6,
    FOREIGN KEY(secret_word_id) REFERENCES correct_words(correct_word_id)
);

CREATE TABLE guesses(
    guess_id INTEGER PRIMARY KEY,
    game_id VARCHAR NOT NULL,
    valid_word_id INTEGER NULL,
    guess_number INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id),
    FOREIGN KEY(valid_word_id) REFERENCES valid_words(valid_word_id)
);

CREATE INDEX games_idx_usernamestate ON games(username, state);
CREATE INDEX valid_words_idx_validword ON valid_words(valid_word);
CREATE INDEX guesses_idx_idnumber ON guesses(game_id, guess_number);


INSERT INTO games(game_id, username, secret_word_id, guess_remaining) VALUES
    ('1', 'dummy', 1, 5),
    ('2', 'dummy', 2, 5),
    ('3', 'money', 3, 5),
    ('4', 'money', 4, 4);


INSERT INTO guesses(game_id, valid_word_id, guess_number) VALUES
    ('1', 1, 1),
    ('2', 2, 1),
    ('3', 3, 1),
    ('4', 4, 1),
    ('4', 5, 2);

COMMIT;

