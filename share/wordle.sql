PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE,
    password VARCHAR
);


COMMIT;
