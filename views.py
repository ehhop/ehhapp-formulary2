import matplotlib
matplotlib.use('Agg')
import pytz, os, shutil, random, string, sys, time, pandas as pd, mpld3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from flask import render_template, flash, send_from_directory, request, redirect, url_for, session
import flask.ext.login as flask_login
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from oauth2client import client as gauthclient
from oauth2client import crypt

from config import *
import database
from __init__ import app, login_manager
from exportInvoiceData import exportrecord
import consolidateRecord
from undo import undo

import_dirname = "import/"

class Auth:
    """Google Project Credentials"""
    CLIENT_ID = google_client_id
    CLIENT_SECRET = google_client_secret
    REDIRECT_URI = redirect_uri
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']

@login_manager.user_loader
def load_user(user_id):
    return database.User.query.get(user_id)
""" OAuth Session creation """

def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    return render_template('login.html', auth_url=auth_url,
                           google_client_id = google_client_id)


@app.route('/gCallback',methods=["POST"])
def googleOAuthTokenVerify():				# authenticate with Google for Icahn accounts
	'''from https://developers.google.com/identity/sign-in/web/backend-auth'''
	token = request.values.get('idtoken', None)
	try:
		idinfo = gauthclient.verify_id_token(token, google_client_id)
		# If multiple clients access the backend server:
		if idinfo['aud'] not in [google_client_id]:
			raise crypt.AppIdentityError("Unrecognized client.")
		if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
			raise crypt.AppIdentityError("Wrong issuer.")
	except crypt.AppIdentityError:
		# Invalid token
		sys.stderr.write("Bad token from client.\n")
		return None
							# okay, now we're logged in. yay!
	userid = idinfo['sub']
	useremail = idinfo['email']
	sys.stderr.write("Token sign in user: " + ", ".join([useremail, userid]) + "\n")
	user = database.User.query.get(useremail)
	if user:					# if user has been here before
		user.authenticated=True			# log them in in DB
		database.ver_db_session.add(user)
		database.ver_db_session.commit()
		flask_login.login_user(user, remember=True)	# log them in in their browser
		session.pop('_flashes', None)
		flash("Logged in.")
	else:
		if ('@icahn.mssm.edu' not in useremail) & ('@mssm.edu' not in useremail):	# not ISMMS account
			return 'Unauthorized e-mail address. You must be a MSSM affiliate with an @icahn.mssm.edu or @mssm.edu address!'
		else:
			user = database.User(email = useremail, tokens=userid)	# create new user in DB
			user.authenticated=True		# log them in in DB
			database.ver_db_session.add(user)
			database.ver_db_session.commit()
			flask_login.login_user(user, remember=True)	# log them in in their browser
			session.pop('_flashes', None)
			flash("Logged in.")
	return useremail				# return logged in email to user


@app.route("/logout", methods=["GET", "POST"])
@flask_login.login_required
def logout():
    """Logout the current user."""
    user = flask_login.current_user
    user.authenticated = False				# log out in db
    database.ver_db_session.add(user)
    database.ver_db_session.commit()
    flask_login.logout_user()				# delete browser cookie
    flash("Logged out.")
    return redirect(url_for("index"))

@app.route("/", methods=['GET'])
@app.route("/index.html", methods=['GET'])
def index():
	#return "HELLO THERE"
	return render_template("index.html")

@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)

@app.route("/medications")
@flask_login.login_required
def view_all_medications():
	#this is an array of type MedicationRecord objects
	year = request.values.get("year","0")
	medications = database.PersistentMedication.query. \
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
	for m in medications:
		m.spend = round(sum([t.qty*t.price for t in m.transactions]),2)
		m.bought = sum([t.qty for t in m.transactions if t.qty>0])
		m.sold = sum([t.qty for t in m.transactions if t.qty<0])
		m.scripts = len(m.transactions)
		m.end_price = round(m.transactions[-1].price,2)
		m.start_price = round(m.transactions[0].price,2)
		m.pct_change = round(m.transactions[-1].price/m.transactions[0].price*100-100,2)

	return render_template("medications.html", year=year,medications=medications)

@app.route("/spending")
@app.route("/piechart")
@flask_login.login_required
def piechart():
	#this is an array of type MedicationRecord objects
	year = request.values.get("year","0")
	medications = database.PersistentMedication.query. \
		order_by(database.PersistentMedication.name.asc()).\
		all()
	if len(medications)==0:
		flash("No medication records in db.")
		return redirect(url_for("view_all_medications"))
	medications = [i.to_class() for i in medications]
	if year!="0":
		medout = []
		for m in medications:
			m.transactions = [t for t in m.transactions if t.date.year==int(year)]
			if len(m.transactions)!=0:
				medout.append(m)
		medications = medout

	plt.style.use('ggplot')
	scale = 0.3
	rcParams['figure.figsize'] = (8*scale,8*scale)
	rcParams['figure.dpi'] = 300
	rcParams["legend.labelspacing"]=0
	rcParams["legend.columnspacing"] = 0
	rcParams["legend.shadow"] = False
	rcParams["legend.frameon"] = False
	rcParams["legend.borderpad"] = 0

	def my_autopct(pct):
	    return ('%.2f%%' % pct) if pct > 1.5 else ''

	med_df = pd.DataFrame([{"name":m.name,
	                        "category":m.category.split(" - ")[0].split(",")[0].strip() if m.category!=None else "Other",
	                        "price_spent":sum([t.price for t in m.transactions])} for m in medications])
	data = med_df.pivot_table(index="category",values="price_spent").\
	sort_values("price_spent",ascending=False)["price_spent"]

	labels = [n if v > data.sum() * 0.015 else '' for n, v in zip(data.index, data)]

	fig, ax1 = plt.subplots(1)
	data.plot.pie(y="price_spent",autopct=my_autopct,labels=labels,title="Dollars spent on medications",label="",ax=ax1,radius=0.6)

	html_figure = mpld3.fig_to_html(fig)

	return render_template("piechart.html", year=year,html_figure=html_figure)

import seaborn as sb

@app.route("/medications/<int:pricetable_id>")
@flask_login.login_required
def view_medication(pricetable_id):
	#this is an array of type MedicationRecord objects
		year = request.values.get("year","2017")
#		if year=="0":
#			year="2017"
		medication = database.PersistentMedication.query. \
			filter_by(pricetable_id=pricetable_id).\
			first_or_404()
		med = medication.to_class()
		if year=="0":
		    year = str(max([t.date.year for t in med.transactions]))
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
#		for tick in ax2.get_xticklabels():
#			tick.set_rotation(45)
		fig.subplots_adjust(hspace=1.5)
		html_figure = mpld3.fig_to_html(fig)
		return render_template("medications_view.html",
				medications=medications,year=year,
		        html_figure=html_figure)

from matplotlib import rcParams
import numpy as np

@app.route("/history/")
@flask_login.login_required
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

			html_figure1 = mpld3.fig_to_html(fig)

			medications = meds

			plt.style.use('ggplot')
			scale = 0.25
			rcParams['figure.figsize'] = (8*scale,8*scale)
			rcParams['figure.dpi'] = 300
			rcParams["legend.labelspacing"]=0
			rcParams["legend.columnspacing"] = 0
			rcParams["legend.shadow"] = False
			rcParams["legend.frameon"] = False
			rcParams["legend.borderpad"] = 0

			def my_autopct(pct):
			    return ('%.2f%%' % pct) if pct > 1.5 else ''

			med_df = pd.DataFrame([{"name":m.name,
			                        "category":m.name,
			                        "price_spent":sum([t.price for t in m.transactions])} for m in medications])
			data = med_df.pivot_table(index="category",values="price_spent").\
			sort_values("price_spent",ascending=False)["price_spent"]

			labels = [n if v > data.sum() * 0.015 else '' for n, v in zip(data.index, data)]

			fig, ax1 = plt.subplots(1)
			data.plot.pie(y="price_spent",autopct=my_autopct,labels=labels,title="Dollars spent on medications",label="",ax=ax1,radius=0.5)

			html_figure2 = mpld3.fig_to_html(fig)
	else:
		meds=[]
		html_figure1=""
		html_figure2=""

	return render_template("medications_view_history.html",
			medications=meds,year=year,
	        html_figure1=html_figure1,html_figure2=html_figure2)

@app.route("/export")
@flask_login.login_required
def displayDownloadButton():
	return render_template("export.html")

@app.route("/export/download", methods = ["GET", "POST"])
@flask_login.login_required
def downloadFile():
	# Download latest invoice file
	# TODO: need to implement sign-in check
	if request.method == "GET":
		if request.args["startDate"] == "" or request.args["endDate"] == "":
			flash('Error: No selected date range.')
			return render_template("export.html")
		else:

			startTimeRange = datetime.strptime(request.args["startDate"], "%m/%d/%Y")
			endTimeRange = datetime.strptime(request.args["endDate"], "%m/%d/%Y")
			# print(startTimeRange)
			# print(endTimeRange)
	else:
		flash('Error: GET error')
		return render_template("export.html")
	# Define name of file to download
	downloadsDir = "downloads"
	downloadFileName = "internalFormularyCosts_"+"from"+startTimeRange.strftime("%m%d%Y")+"to"+endTimeRange.strftime("%m%d%Y")+"_"+str(int(time.time()))+".xlsx"
	exportSuccessful = exportrecord(downloadFileName, startTimeRange, endTimeRange)
	if exportSuccessful:
		return send_from_directory(downloadsDir, downloadFileName, as_attachment=True)
	else:
		flash('Error: Date range longer than 1 year')
		return render_template("export.html")


@app.route("/import", methods=["GET","POST"])
@flask_login.login_required
def upload_invoice():
	if request.method == 'POST' and "invoice_file" in request.files:
		for invoice_file_data in request.files.getlist('invoice_file'):
			if invoice_file_data:
				invoice_filename_ext = invoice_file_data.filename.split(".")[-1]
				if invoice_filename_ext == "xls":
					invoice_filename = "invoice-upload-"+str(int(time.time()))+".xls"
				elif invoice_filename_ext == "xlsx":
					invoice_filename = "invoice-upload-"+str(int(time.time()))+".xlsx"
				else:
					print(invoice_filename_ext)
					flash("Error: %s is not an Excel .xls or .xlsx file"%invoice_file_data.filename)
					continue
				invoice_file_data.save(import_dirname+invoice_filename)
				msg,status = consolidateRecord.main(import_dirname+invoice_filename,uploaded_name = invoice_file_data.filename)
				if status:
					flash('Invoice added to db.')
				else:
					flash("Error: %s" % str(msg))
			else:
				flash('Error: No selected file.')
		return redirect(url_for("upload_invoice"))
	return render_template("import.html")

@app.route("/invoices/", methods=["GET"])
@flask_login.login_required
def view_all_invoices():
	invoices = database.Invoice.query.all()
	for invoice in invoices:
		invoice.dates = sorted([i.requisition_date for i in invoice.records])
	return render_template("invoices.html",invoices=invoices)

@app.route("/invoices/<int:invoice_id>/download", methods=["GET"])
@flask_login.login_required
def download_invoice(invoice_id):
	invoice = database.Invoice.query.get_or_404(invoice_id)
	return send_from_directory("", invoice.filename, as_attachment=True, attachment_filename=invoice.properties_dict()["uploaded_name"])

@app.route("/invoices/<int:invoice_id>/view", methods=["GET"])
@flask_login.login_required
def view_invoice_records(invoice_id):
	invoice = database.Invoice.query.get_or_404(invoice_id)
	return render_template("view_invoice.html",invoice=invoice)

@app.route("/invoices/<int:invoice_id>/delete",methods=["POST"])
@flask_login.login_required
def delete_invoice(invoice_id):
	invoice = database.Invoice.query.get_or_404(invoice_id)
	undo(invoice.checksum)
	flash("Deleted invoice %s"%invoice.properties_dict()["uploaded_name"])
	return redirect(url_for("view_all_invoices"))

def randomword(length):
        '''generate a random string of whatever length, good for filenames'''
        return ''.join(random.choice(string.ascii_lowercase) for i in range(length))
