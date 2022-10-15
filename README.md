# Backend APIs for Wordle App

Project entails APIs required for playing Wordle. Programming language is Python and Quart micro-framework is used for developing APIs. Hypercorn is used along with Quart to expose APIs. Data is stored in sqlite3

How to run the project:

- Go to project directory
- Run the command ```./bin/init.sh``` to initialize the database
- Run the command ```foreman start``` to start the application server
- Run API using any API client like httpie or curl
- Check the list of APIs [here](http://127.0.0.1:5000/docs) generated by Quart Schema