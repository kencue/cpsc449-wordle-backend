DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE,
    password VARCHAR NOT NULL
);


INSERT INTO users(username, password)
values
    ('dummy', 'abc'),
    ('money', 'abc');