#!/home/rneff/anaconda3/bin/python3

'''
__init__.py

Holds the config params and starts the Flask web app
for this python formulary library
so that we can render it as a web service in the future

Made by Ryan Neff 11/21/17
'''

from config import *

import os, json, datetime

from flask import Flask, request, redirect, send_from_directory, \
	Response, stream_with_context, url_for, render_template, \
	session
from flask_mail import Mail
from requests.auth import HTTPBasicAuth
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = flask_secret_key
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

import database
import invoicerecord
import consolidateRecord
import exportInvoiceData
from views import *

@app.teardown_appcontext
def shutdown_session(exception=None):
    database.ver_db_session.remove()

if __name__=="__main__":
	#start the web server if run directly
	app.run(debug=True, port=5000)
