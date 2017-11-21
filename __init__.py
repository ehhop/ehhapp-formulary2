#!/usr/bin/env python

'''
__init__.py

Holds the config params and starts the Flask web app 
for this python formulary library
so that we can render it as a web service in the future

Made by Ryan Neff 11/21/17
'''

from flask import Flask

sqlalchemy_db = "sqllite://formulary.db"
flask_secret_key = ""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = flask_secret_key

if __name__=="__main__":
	#start the web server if run directly
	app.run(debug=True)