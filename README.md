# CPSC 449 Project 3
[Project 3](https://docs.google.com/document/d/1OWltxCFRsd2s4khOdfwKLZ3vqF6dsJ087nyMn0klcQs/edit) involves extending the mock Wordle backend application from [Project 1](https://docs.google.com/document/d/14YzD8w5SpJk0DqizgrgyOsXvQ2-rrd-39RUSe2GNvz4/edit) and [Project 2](https://docs.google.com/document/d/1BXrmgSclvifgYWItGxxhZ72BrmiD5evXoRbA_uRP_jM/edit#) to include the following objectives:
- Adding replica databases for the games service while maintaining load balancing
- Adding a leaderboard service that uses a different database system (i.e. Redis)

This project also builds upon concepts introduced in [Exercise 2](https://docs.google.com/document/d/1-tFBfCP2rhk5YFtXYpGD894Ghy4UY-J3o9Zs7abbS8c/edit) and [Exercise 3](https://docs.google.com/document/d/14i8cpm7z1oFh5y5gmAkQ39AH3Pu8oWRr6B6TOziGYhY/edit) with regards to configuring the replicas and using Redis in Python.

### Authors
Section 02
Group 20
Members:
- Abhishek Nagesh Shinde
- Alejandro Ramos Jr
- Ken Cue
- Michael Morikawa

## Setting Up
### Development Environment 
Tuffix 2020 (Linux)

### Application Prerequisites
- Python
- Nginx
- Quart
- Sqlite3 (== v1.4.41)
- Foreman
- Redis (redis-py & Hiredis)
- Databases
- Quart-Schema
- Curl
- HTTPie

***Important Note: Please make sure all these are installed in the system (through pip or apt-get) before setting up the project***

### VHost Setup
1. Make sure that nginx is running in the background
```
$ sudo service nginx status
```
2. Verify that `tuffix-vm` is in `/etc/hosts`
```
$ cat /etc/hosts
```
__Note:__ This project uses the hostname `tuffix-vm`. 
3. Copy the VHost file in `/share` to `/etc/nginx/sites-enabled` then restart nginx 
```
$ sudo cp share/wordle /etc/nginx/sites-enabled/wordle
$ sudo service nginx restart
```

### Initializing and Starting the Application
1. Go to the project's directory
2. Start the app with Foreman
```
$ foreman start
```
3. After making sure the app is running in the background, run the command below to initialize databases and populate them with values.
```
$ ./bin/init.sh
```
***Important Note: If you run into permission issues (i.e. forbidden errors) in Step 2, run both the Foreman step and initialization step with root privilege by adding `sudo` before the command***

## REST API Features
- Register a user (includes password hashing)
- Authenticate a user (includes hashing verification)
- Start a new game
- Guess a five-letter word
- Retrieve the state of a game in progress
- List the games in progress for a user
- Check the statistics for a particular user
- Display the top 10 scores in the leaderboard
- Report score to the leaderboard _(not public facing)_

## Running the Application

### Registering a User
After starting up the app, create an initial user using the following command with HTTPie where `<username>` and `<password>` are custom values (will need them later when logging in):
```
$ http POST http://tuffix-vm/register username=<username> password=<password>
```
The whole application can only be accessed after authentication, so use the username and password that was created in this step.


### Using Quart-Schema Documentation
The API documentation generated by Quart-Schema can be accessed with [this link](http://tuffix-vm/docs) or typing the URL `http://tuffix-vm/docs`. Note that this is only for the Game endpoint.


### Using HTTPie
In order to run via httpie, use the following the commands:
- Creating a user
```
$ http POST http://tuffix-vm/register username=<username> password=<password>
```
- Authenticating a user
```
$ http GET http://tuffix-vm/ --auth <username>:<password>
```
- Creating a game 
```
$ http POST http://tuffix-vm/games --auth <username>:<password>
```
- Checking the state of a game 
```
$ http GET http://tuffix-vm/games/<game_id> --auth <username>:<password>
```
- Playing a certain game/making a guess
```
$ http POST http://tuffix-vm/games/<game_id> guess=<5-letter-word> --auth <username>:<password>
```
- Retrieving a list of in-progress games
```
$ http GET http://tuffix-vm/games/ --auth <username>:<password>
``` 
- Check the statistics of the user 
```
http GET http://tuffix-vm/games/statistics --auth <username>:<password>
```

