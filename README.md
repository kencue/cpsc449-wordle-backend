# CPSC 449 Project 4
[Project 4](https://docs.google.com/document/d/19BqaDN9M9fMfw6WjwISGDauF_I2w20UJ4lNmW9USbn0/edit) builds upon the previous project by adding a connection between the games and leaderboard service through webhooks. Some of the solutions presented here have been touched upon in [Exercise 4](https://docs.google.com/document/d/1GeF5txkEb3Jl0_YtnFKFh21xiDff1IJ54XC9Qydk3GE/edit).

All of the concepts presented here were taken from the [Fall 2022 CPSC 449 Course](https://sites.google.com/view/cpsc-449).

### Links to Previous Projects & Exercises Prompts
- [Project 1](https://docs.google.com/document/d/14YzD8w5SpJk0DqizgrgyOsXvQ2-rrd-39RUSe2GNvz4/edit)
- [Project 2](https://docs.google.com/document/d/1BXrmgSclvifgYWItGxxhZ72BrmiD5evXoRbA_uRP_jM/edit)
- [Project 3](https://docs.google.com/document/d/1OWltxCFRsd2s4khOdfwKLZ3vqF6dsJ087nyMn0klcQs/edit)
- [Exercise 2](https://docs.google.com/document/d/1-tFBfCP2rhk5YFtXYpGD894Ghy4UY-J3o9Zs7abbS8c/edit)
- [Exercise 3](https://docs.google.com/document/d/14i8cpm7z1oFh5y5gmAkQ39AH3Pu8oWRr6B6TOziGYhY/edit)

### Authors
Section 02
Group 13
Members:
- Abhishek Nagesh Shinde
- Ken Cue
- Yash Gandhi


## Setting Up
### Development Environment 
Tuffix 2020 (Linux)


### Application Prerequisites
- Python
- Nginx
- Quart
- Sqlite3 (== v1.4.41)
- Foreman
- Redis (including redis-py & Hiredis)
- Databases
- Quart-Schema
- Curl
- HTTPie
- RQ
- HTTPX

***Note: Please make sure all these are installed in the system (through pip or apt-get) before setting up the project***


### VHost Setup
1. Make sure that nginx is running in the background
```
$ sudo service nginx status
```

2. Verify that `tuffix-vm` is in `/etc/hosts`
```

$ cat /etc/hosts
```
***Note: This project uses the hostname `tuffix-vm`.***

3. Copy the VHost file in `/share` to `/etc/nginx/sites-enabled` then restart nginx 
```
$ sudo cp share/wordle /etc/nginx/sites-enabled/wordle
$ sudo service nginx restart
```


### Initializing and Starting the Application
1. Go to the project's directory

2. Download the latest stable release of [LiteFS](https://github.com/superfly/litefs/releases), and extract the `litefs` binary into the `./bin` directory. Verify that it is installed properly by running the command below, which should return `config file not found`.
```
$ ./bin/litefs
```
***Note: the LiteFS releases includes pre-released beta versions. We recommend you scroll down to find the actual release versions.***

3. Start the app with Foreman
```
$ foreman start
```

4. After making sure the app is running in the background, run the command below to initialize databases and populate them with values.
```
$ ./bin/init.sh
```
***Important Note: If you run into permission issues (i.e. forbidden errors) in Step 3, run both the Foreman step and initialization step (Steps 3 & 4) with root privilege by adding `sudo` before the command***

5. The app uses the default configuration `127.0.0.1:6379`. Make sure the port isn't used by another service and verify that Redis is running.
```
$ redis-cli ping
```
If it is not returning `PONG`, check if Redis was properly installed/configured.

### Retrying Failed jobs
***About Cron - Cron is a daemon that runs scheduled tasks (also known as "cron jobs") at predetermined times. These tasks are specified in the configuration file called the crontab, which can be edited by the user to schedule tasks to run automatically.***

Each line in the crontab file represents a specific task and follows a specific syntax:

You can find the crontab file under 
`/Project4/branch/cpsc449-wordle-backend/crontab.txt`

```
$ */10 * * * * run-one rq requeue --all --queue default
```
Here astrisks represents The asterisks represent the following elements:
    Minute (0-59)
    Hour (0-23)
    Day of the month (1-31)
    Month (1-12)
    Day of the week (0-6, with 0 representing Sunday)

Run 
```
$ */10 * * * * run-one rq requeue --all --queue default
```
to retry the failed running jobs "Redis Queue (rq)" to requeue and retry them and run after 10 minutes (represented in first astrisk as "10")


## REST API Features
- Register a user (includes password hashing)
- Authenticate a user (includes hashing verification)
- Start a new game
- Guess a five-letter word
- Retrieve the state of a game in progress
- List the games in progress for a user
- Check the statistics for a particular user
- Display the top 10 scores in the leaderboard (public-facing, no authentication needed)
- Report score to the leaderboard
- Adding a webhook for games service to report game statistics to


## Running the Application

### Registering a User
After starting up the app, create an initial user using the following command with HTTPie where `<username>` and `<password>` are custom values (will need them later when logging in):
```
$ http POST http://tuffix-vm/register username=<username> password=<password>
```
The whole application can only be accessed after authentication, so use the username and password that was created in this step.


### Using Quart-Schema Documentation
The API documentation generated by Quart-Schema can be accessed with [this link](http://tuffix-vm/docs) or typing the URL `http://tuffix-vm/docs`. Note that this is only for the Game endpoint. In order to access the docs endpoints for the User and Leaderboard services, you must access directly to the ports 5000 for the User service ([link](http://127.0.0.1:5000/docs)) and 5400 for the Leaderboard service ([link](http://127.0.0.1:5400/docs)).


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
- Publicly display the top 10 scores in the leaderboard
```
http GET http://tuffix-vm/leaderboard/top10
```
- Report score to the leaderboard
```
http POST http://127.0.0.1:5400/leaderboard/add game_id=<game_id> is_win=<true/false> number_of_guesses=<num_guesses> username=<username>
```
_Note: this accesses the leaderboard service directly at `127.0.0.1:5400` and not through Nginx as this endpoint will not be visible to the public_
- Adding a webhook for games service to report game statistics to
```
http POST http://tuffix-vm/webhooks/register callback_url=<url>
```