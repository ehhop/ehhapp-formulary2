from __init__ import app
from flask import render_template, flash, send_from_directory
import flask.ext.login as flask_login
from oauth2client import client as gauthclient
from oauth2client import crypt
import pytz, os, shutil, random, string, sys
from datetime import datetime, timedelta
import database
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mpld3
import pandas as pd

@app.route("/", methods=['GET'])
@app.route("/index.html", methods=['GET'])
def index():
	#return "HELLO THERE"
	return render_template("index.html")

@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)

@app.route("/invoices/new")
def add_invoice():
  #todo
  return "#TODO"

@app.route("/medications")
def view_all_medications():
	#this is an array of type MedicationRecord objects
	medications = database.PersistentMedication.query.\
		order_by(database.PersistentMedication.name.asc()).\
		all()
	medications = [i.to_class() for i in medications]
	return render_template("medications.html", 						medications=medications)

@app.route("/medications/<int:pricetable_id>")
def view_medication(pricetable_id):
	#this is an array of type MedicationRecord objects
        medication = database.PersistentMedication.query.\
		filter_by(pricetable_id=pricetable_id).\
		first_or_404()
        med = medication.to_class()
        medications = [medication.to_class()]
        fig, ax = plt.subplots()
        df = pd.DataFrame([{"date":t.date,"price":t.price} for t in med.transactions])
        df.plot(x="date",y="price",marker='o',ax=ax)
        html_figure = mpld3.fig_to_html(fig)
        return render_template("medications_view.html", 
				medications=medications,
                                html_figure=html_figure)
