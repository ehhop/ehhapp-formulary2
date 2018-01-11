from __init__ import app
from flask import render_template, flash, send_from_directory
import flask.ext.login as flask_login
from oauth2client import client as gauthclient
from oauth2client import crypt
import pytz, os, shutil, random, string, sys
from datetime import datetime, timedelta

@app.route("/", methods=['GET'])
@app.route("/index.html", methods=['GET'])
def index():
	#return "HELLO THERE"
	return render_template("index.html")

@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)