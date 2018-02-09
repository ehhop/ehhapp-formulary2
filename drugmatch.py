#!/usr/bin/python
import os
import sys
import requests
import json
import urllib2
import simplejson
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

def rxGetDrugProperties(name,mfgID = None):
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
        print "Completed Analysis: "+common_name
        return dosage, admin, common_name
    except:
		if (mfgID != None):
			return rxGetDrugProperties(backupSearch(mfgID))
		return -1, -1, -1

def backupSearch(mfgID):
	API_KEY = '5c307a27-6d44-4c69-9110-b9c1d0ba3186'
	REST_URL = "http://data.bioontology.org"

	opener = urllib2.build_opener()
	opener.addheaders = [('Authorization', 'apikey token=' + API_KEY)]
	resources = json.loads(opener.open(REST_URL + "/").read())
	print resources
    #return propertyJSON['propConceptGroup']['propConcept'][0]['propValue']

if __name__ == '__main__':
    print connectionCheck()
    #print rxGetDrugProperties("LISINOPRIL 10MG TAB BOTTLE")
    #print rxGetDrugProperties("FLUOCINONIDE CREAM 0.05% 30GM")
    print rxGetDrugProperties("VENTOLIN HFA 90MCG INH 18GM - OPD ONLY","00173068220")
    #print rxGetNDC("SODIUM BICARBONATE 650MG TAB")
