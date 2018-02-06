from __init__ import app
from flask import render_template, flash, send_from_directory, request, redirect, url_for
import flask.ext.login as flask_login
from oauth2client import client as gauthclient
from oauth2client import crypt
import pytz, os, shutil, random, string, sys
from datetime import datetime, timedelta
import database
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random, string, time
import pandas as pd
import mpld3
from exportInvoiceData import exportrecord
import consolidateRecord 
import_dirname = "import/"

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
		fig, (ax1,ax2) = plt.subplots(2)
		if med.transactions[0].price < 1:
			df = pd.DataFrame([{"date":t.date,"price":t.price*100,"qty":t.qty} for t in med.transactions])
			df.plot(x="date",y="price",marker='o',ax=ax1)
			ax1.set_title("Price history")
			ax1.set_ylabel("Price per 100 ($)")
			ax1.set_xlabel("Date")
		else:
			df = pd.DataFrame([{"date":t.date,"price":t.price,"qty":t.qty} for t in med.transactions])
			df.plot(x="date",y="price",marker='o',ax=ax1)
			ax1.set_title("Price history")
			ax1.set_ylabel("Price ($)")
			ax1.set_xlabel("Date")
		df.groupby([df["date"].dt.year, df["date"].dt.month,df["date"].dt.day])["qty"].sum().plot(kind="bar",ax=ax2)
		ax2.set_title("Medication volume")
		ax2.set_ylabel("Doses given")
		ax2.set_xlabel("Date")
		fig.subplots_adjust(hspace=1.5)
		html_figure = mpld3.fig_to_html(fig)
		return render_template("medications_view.html", 
				medications=medications,
		                        html_figure=html_figure)

@app.route("/export")
def displayDownloadButton():
	return render_template("export.html")

@app.route("/export/download", methods = ["GET", "POST"])
def downloadFile():
	# Download latest invoice file
	# TODO: need to implement sign-in check

	# Do we need to worry about security for bad filename if we're just downloading?
	downloadsDir = "downloads"
	downloadFileName = "internalFormularyCosts-"+str(int(time.time()))+".xlsx"

	if request.method == "POST":
		if request.form["startDate"] == "" or request.form["endDate"] == "":
			flash('Error: No selected date range.')
			return render_template("export.html") 
		else:
			startTimeRange = datetime.strptime(request.form["startDate"], "%m/%d/%Y %I:%M %p")
			endTimeRange = datetime.strptime(request.form["endDate"], "%m/%d/%Y %I:%M %p")
			print(startTimeRange)
			print(endTimeRange)
	else:
		flash('Error: Post error')

	exportrecord(downloadFileName, startTimeRange, endTimeRange)
	return send_from_directory(downloadsDir, downloadFileName, as_attachment=True)

@app.route("/import", methods=["GET","POST"])
def upload_invoice():
	if request.method == 'POST':
		invoice_file_data = request.files['invoice_file']
		if invoice_file_data.filename == '':
			flash('Error: No selected file.')
			return render_template("import.html")
		if invoice_file_data:
			invoice_filename = "invoice-upload-"+str(int(time.time()))+".xlsx"
			invoice_file_data.save(import_dirname+invoice_filename)
			msg,status = consolidateRecord.main(import_dirname+invoice_filename)
			if status:
				flash('Invoice added to db.')
				return redirect(url_for("view_all_medications"))
			else:
				flash("Error: %s" % str(msg))
		else:
			flash('Error: No selected file.')
	return render_template("import.html")

def randomword(length):
        '''generate a random string of whatever length, good for filenames'''
        return ''.join(random.choice(string.lowercase) for i in range(length))
