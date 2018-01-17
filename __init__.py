#!/home/rneff/anaconda3/bin/python3

'''
__init__.py

Holds the config params and starts the Flask web app 
for this python formulary library
so that we can render it as a web service in the future

Made by Ryan Neff 11/21/17
'''

from flask import Flask, request, redirect, send_from_directory, Response, stream_with_context, url_for, render_template
from flask_mail import Mail
from requests.auth import HTTPBasicAuth

sqlalchemy_db = "sqlite:///formulary.db"
flask_secret_key = "flask-test-ehhop"

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = flask_secret_key

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
