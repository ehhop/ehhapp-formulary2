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
	year = request.values.get("year","0")
	medications = database.PersistentMedication.query.\
		order_by(database.PersistentMedication.name.asc()).\
		all()
	medications = [i.to_class() for i in medications]
	if year!="0":
		medout = []
		for m in medications:
			m.transactions = [t for t in m.transactions if t.date.year==int(year)]
			if len(m.transactions)!=0:
				medout.append(m)
		medications = medout
	return render_template("medications.html", year=year,medications=medications)

import seaborn as sb

@app.route("/medications/<int:pricetable_id>")
def view_medication(pricetable_id):
	#this is an array of type MedicationRecord objects
		year = request.values.get("year","2017")
		if year=="0":
			year="2017"
		medication = database.PersistentMedication.query.\
			filter_by(pricetable_id=pricetable_id).\
			first_or_404()
		med = medication.to_class()
		med.transactions = [t for t in med.transactions if t.date.year==int(year)]
		medications = [med]
		fig, (ax1,ax2) = plt.subplots(2)
		idx = pd.date_range(year+'-01-01 00:00:00', freq='W', periods=52)
		plt.style.use('ggplot')
		scale = .4
		rcParams['figure.figsize'] = (20*scale,8*scale)
		rcParams['figure.dpi'] = 150
		rcParams["legend.labelspacing"]=0
		rcParams["legend.columnspacing"] = 0
		rcParams["legend.shadow"] = False
		rcParams["legend.frameon"] = False
		rcParams["legend.borderpad"] = 0
		
		df = pd.DataFrame([{"date":t.date,"price":t.price,"qty":t.qty} for t in med.transactions if t.date.year==int(year)])
		if len(df)==0:
			flash("No data for that year.")
			return redirect(url_for("view_all_medications"))
		df.set_index("date",inplace=True)
		if med.transactions[0].price < 1:
			prices = df[["price"]].resample('W').mean().loc[idx,].fillna(method='ffill').fillna(method='bfill')*100
		else:
			prices = df[["price"]].resample('W').mean().loc[idx,].fillna(method='ffill').fillna(method='bfill')
		prices.plot(ax=ax1)
		ax1.set_title("Price history")
		if med.transactions[0].price < 1:
			ax1.set_ylabel("Price per 100 ($)")
		else:
			ax1.set_ylabel("Price ($)")
		ax1.set_xlabel("Date")
		volume = df[["qty"]].resample('W').sum().loc[idx,].fillna(0)
		volume.plot(kind="bar",ax=ax2)
		ax2.set_title("Medication volume")
		ax2.set_ylabel("Doses given")
		ax2.set_xlabel("Date")
		for tick in ax2.get_xticklabels():
			tick.set_rotation(45)
		fig.subplots_adjust(hspace=1.5)
		html_figure = mpld3.fig_to_html(fig)
		return render_template("medications_view.html", 
				medications=medications,year=year,
		        html_figure=html_figure)

from matplotlib import rcParams
import numpy as np

@app.route("/history/")
def view_medication_history(year=None,search_term = None):
	search_term = request.values.get("search_term",None)
	year = request.values.get("year","2017")
	plt.style.use('ggplot')
	scale = .4
	rcParams['figure.figsize'] = (20*scale,8*scale)
	rcParams['figure.dpi'] = 150
	rcParams["legend.labelspacing"]=0
	rcParams["legend.columnspacing"] = 0
	rcParams["legend.shadow"] = False
	rcParams["legend.frameon"] = False
	rcParams["legend.borderpad"] = 0
	#rcParams['font.size'] = 12
	#rcParams['font.family'] = 'DejaVu Sans'
	#plt.style.use('seaborn-bright')

	if search_term:
			meds = []
			if ";" in search_term:
				search_terms = search_term.split(";")
				search_terms = [i.strip().upper() for i in search_terms]
				for m in search_terms:
					med_result = database.PersistentMedication.query.filter(database.PersistentMedication.name.contains(m)).all()
					med_result = [i.to_class() for i in med_result]
					meds.extend(med_result)
			else:
				med_to_chart = search_term.strip().upper()
				meds = database.PersistentMedication.query.filter(database.PersistentMedication.name.contains(med_to_chart)).all()
				meds = [i.to_class() for i in meds]
			
			idx = pd.date_range(year+'-01-01 00:00:00', freq='MS', periods=12)
			price_df = pd.DataFrame(index=idx)
			#print(idx)
			medout = []
			for med in meds:
				med.transactions = [t for t in med.transactions if (t.date.year==int(year))&(t.qty>0)]
				if med.transactions != []:
					medout.append(med)
				df = pd.DataFrame([{"date":t.date,"price":t.price,"qty":t.qty} for t in med.transactions])	
				if len(df)>0:
					df.set_index("date",inplace=True)
					prices = df[["price"]].resample('MS').mean().loc[idx,].fillna(method='ffill').fillna(method='bfill')
					price_df[med.name[0:20]] = prices
			if len(price_df)==0:
				meds=[]
				html_figure=""
				flash("No data in db for that search, please try again.")
				return render_template("medications_view_history.html", 
						medications=meds,year=year,
						html_figure=html_figure)
			meds = medout
			prices = price_df.copy(deep=True)

			fig, (ax1,ax2) = plt.subplots(1,2)
			colors = plt.cm.Paired(np.linspace(0, 1, len(price_df)))

			for col in range(0,len(prices.columns)):
				for row in range(1,len(prices.index)):
					prices.iloc[row][col] = ((prices.iloc[row][col] - prices.iloc[0][col]) / prices.iloc[0][col]) * 100
				prices.iloc[0][col] = 0
			prices.plot(marker="o",title="Percent change from Jan "+year,colors=colors,ax=ax1)
			ax1.set_ylabel("% change")
			ax1.legend(fontsize = 10,shadow=False,framealpha=0,loc="best")

			price_df_100 = price_df.copy(deep=True)
			price_df_100.plot(marker="o",title="Monthly price for "+year,colors=colors,ax=ax2)
			ax2.set_ylabel("Price per dose ($)")
			ax2.legend_.remove()

			html_figure = mpld3.fig_to_html(fig)
	else:
		meds=[]
		html_figure=""

	return render_template("medications_view_history.html", 
			medications=meds,year=year,
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
	if request.method == 'POST' and "invoice_file" in request.files:
		for invoice_file_data in request.files.getlist('invoice_file'):
			if invoice_file_data:
				invoice_filename = "invoice-upload-"+str(int(time.time()))+".xlsx"
				invoice_file_data.save(import_dirname+invoice_filename)
				msg,status = consolidateRecord.main(import_dirname+invoice_filename)
				if status:
					flash('Invoice added to db.')
				else:
					flash("Error: %s" % str(msg))
			else:
				flash('Error: No selected file.')
		return redirect(url_for("upload_invoice"))
	return render_template("import.html")

def randomword(length):
        '''generate a random string of whatever length, good for filenames'''
        return ''.join(random.choice(string.lowercase) for i in range(length))
