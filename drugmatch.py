#!/usr/bin/python
import os
import sys
import requests
import json
import urllib as urllib2
import simplejson
from pprint import pprint
from zeep import Client
'''
Pull closest available drug information from string name using federal database save_persistent_record
'''

def connectionCheck():
	url = 'http://rxnav.nlm.nih.gov/REST/version'
	header = {'Accept': 'application/json'}
	getCheck = requests.get(url, headers=header)
	if getCheck.status_code != requests.codes.ok:
		response = "RXNorm server response error. Response code: %s" % getCheck.status_code
	else:
		response = "Connection check complete. RXNorm online. Response code: %s" % getCheck.status_code
	return response

def rxGetDrugProperties(name,mfgID = None, cui = None):

	if (cui == None):
		client = Client('https://rxnav.nlm.nih.gov/RxNormDBService.xml')
		result = str(client.service.getApproximateMatch(name, 0, 0 ))
		result = result.partition("RXCUI")[2]
		result = result.partition("_value_1': '")[2]
		result = result.partition("',")[0]
		cui = result #Hopefully we got the right one from the matching!


	baseurl = 'http://rxnav.nlm.nih.gov/REST/RxTerms/rxcui/'
	#return cui
	#result2 = str(client.service.getAllHistoricalNDCs(cui,0))


	#print cui
	#baseurl = 'http://rxnav.nlm.nih.gov/REST/'
	#rxCuiSearch = 'rxcui/'
	#rxPropertySearch = '/property?propName='
	#rxQuantitySearch = 'AVAILABLE_STRENGTH'

	#Request JSON return
	header = {'Accept' : 'application/json'}

	getProperty = requests.get(baseurl+cui+'/allinfo', headers = header)
	propertyJSON = json.loads(getProperty.text, encoding = "utf-8")


	try:
		dosage = propertyJSON['rxtermsProperties']['strength']
		admin = propertyJSON['rxtermsProperties']['route']
		common_name = propertyJSON['rxtermsProperties']['displayName']

		common_name = common_name.partition("(")[0]
		print("DrugMatch - Drug:"+name+" Identified Successfully: "+common_name)
		return dosage, admin, common_name, cui
	except:
		if (mfgID != None):
			print("DrugMatch - Drug:"+name+" Not Found, Attempting Workaround...")
			return rxGetDrugProperties(name, cui = backupSearch(mfgID))
		print("DrugMatch - Drug:"+name+" Could Not Be Identified")
		return None, None, None, None
def get_json(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('Authorization', 'apikey token=' + '5c307a27-6d44-4c69-9110-b9c1d0ba3186')]
	return json.loads(opener.open(url).read())

def backupSearch(mfgID):
	API_KEY = '5c307a27-6d44-4c69-9110-b9c1d0ba3186'
	REST_URL = "http://data.bioontology.org/search?q="
	ONT_URL = "https://bioportal.bioontology.org/ontologies/DRON?p=classes&conceptid="


	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('Authorization', 'apikey token=' + API_KEY)]
		resources = json.loads(opener.open(REST_URL + mfgID+"").read())
		targetID = resources['collection'][0]["@id"]

		#Read the raw URL resulting
		f= urllib2.urlopen(ONT_URL + targetID).read()
		f = f.partition("has_proper_part")[2].partition('data-cls="')[2].partition('"')[0]
		f = urllib2.urlopen(ONT_URL + f).read()
		f = f.partition("has_RxCUI")[2].partition("<p>")[2].partition("</p>")[0]
		return f
	except:
		return "-1"

	'''
# Get the name and ontology id from the returned list
	ontology_output = []
	for ontology in ontologies:
		ontology_output.append(ontology["name"] + "\n" + ontology["@id"] + "\n\n")

	# Print the first ontology in the list
	print ontology_output

	#return propertyJSON['propConceptGroup']['propConcept'][0]['propValue']
	'''
if __name__ == '__main__':
	pass
	print(rxGetDrugProperties("PANTOPRAZOLE 40MG TAB","00008084181"))
	print(rxGetDrugProperties("VENTOLIN HFA 90MCG INH 18GM - OPD ONLY","00173068220"))
	#print connectionCheck()
	#print rxGetDrugProperties("VENTOLIN HFA 90MCG INH 18GM - OPD ONLY","00173068220")
