#!/usr/bin/env python
'''
Description: reads EHHOP formularly invoice in .xls format
Inputs: EHHOP formularly invoice in .xls standard format
Output: Consolidated formulary invoice record with summed issues in .csv format

11/20/2017 Daniel Charytonowicz
'''
import os, collections, invoicerecord, csv, database, numpy
from datetime import datetime
import collections
import invoicerecord
from invoicerecord import MedicationRecord
import database
import pandas as pd
import datetime, json
import drugmatch
import time

actualcolumns= ["Exp Code",  #these are the column names in our Invoice file headers
                "Supply Loc",
                "Item No",
                "Item Description",
                "Vendor Name",
                "Vendor Ctlg No",
                "Mfr Name",
                "Mfr Ctlg No",
                "Comdty Name ",
                "Comdty Code",
                "Requisition No",
                "Requisition Date",
                "Issue Qty",
                "UM",
                "Price",
                "Extended Price",
                "Cost Center No"]

invoice_columns = ['exp_code',  #these are columns that correspond to our invoice in the DB
                 'supply_loc',
                 'item_no',
                 'item_description',
                 'vendor_name',
                 'vendor_ctg_no',
                 'mfr_name',
                 'mfr_ctlg_no',
                 'comdty_name',
                 'comdty_code',
                 'requisition_no',
                 'requisition_date',
                 'issue_qty',
                 'um',
                 'price',
                 'extended_price',
                 'cost_center_no']


## from https://www.pythoncentral.io/hashing-files-with-python/
import hashlib
def hash_file(filename):
    '''creates hashes from files so that we can uniquely identify uploads'''
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def saveinvoicetodb(file, uploaded_name=""):
    '''takes a invoice file, checks the hash, adds invoice records, and saves to persistentmedications'''
    ds = pd.read_excel(file,usecols=range(0,17))
    ds = ds.dropna(axis=0,thresh=len(ds.columns)-3)
    ds = ds[[col for col in actualcolumns if col in ds.columns]]
    invoiceobjs = []
    hashMe = hash_file(file)
    invoice_db, is_imported = database.get_or_create(database.Invoice,checksum=hashMe) #check if invoice already was uploaded
    if is_imported: #if so, reject invoice and return here
        return False,hashMe
    # if not, populate invoice object
    properties = {"uploaded_name":uploaded_name}
    invoice_db.properties = json.dumps(properties)
    invoice_db.filename=file
    invoice_db.date_added = datetime.datetime.now()
    for ix,row in ds.iterrows(): #populate invoicerecords with data from invoice's rows
        ## FOR ROW IN THE INVOICE ##
        newobj = database.InvoiceRecord(invoice_id=invoice_db.id) #create a new DB InvoiceRecord obj
        for df_col in ds.columns: #for column in invoice's  row
            col = invoice_columns[actualcolumns.index(df_col)] #convert the column name to the one we want for the DB
            setattr(newobj,col,str(row[df_col])) #set the property of InvoiceRecord to the column that correpsonds to it
            #print(col,getattr(newobj,col))
        #break
        invoice_db.records.append(newobj) #we append all of the invoicerecords to the Invoice DB object for later

    data = dict() ## ???

    originInvoiceHash = hashMe
    for ix,row in ds.iterrows(): #iterate through each row in invoice XLS (WHY NO INVOICERECORD HERE WTF)
        pricetable_id = int(row["Item No"])           #Medication ID

        if numpy.isnan(pricetable_id): #if no pricetable id, it's useless
            continue

        medication_name = row["Item Description"]         #Medicaction Name
        mfgID = row["Mfr Ctlg No"] if "Mfr Ctlg No" in row else ""
        qty = int(row["Issue Qty"])             #Quantity of Medication issued
        price = float(row["Extended Price"])/qty       #Medication price
        date_issued = row["Requisition Date"]
        category = row["Comdty Name "] if "Comdty Name " in row else "" #this is a bug in older invoices that we handle (e.g. circa 2014-2015)
        date_issued = date_issued.to_pydatetime()

        #Insantiate a new Medication record
        record = MedicationRecord(pricetable_id = pricetable_id, \
            name = medication_name,\
            category=category,\
            transactions = [MedicationRecord.transaction(date = date_issued,price = price,qty = qty,originInvoiceHash = originInvoiceHash)])
        #Check if the record has already been created for that med, else make a new one
        if record in data:
            #since the record is in the database, update transactions
            old_record = data[record]
            old_record.transactions += record.transactions
        else:
            #Add record to dict of MedicationRecords
            data[record] = record #hold temporary MedicationRecords

    #print("HashOrigin Is:"+str(originInvoiceHash))
    persistentmeds = []
    for key, value in data.items():
        #print value.transactions
        persistent_med = database.save_persistent_record(value, commit=False)
        print(persistent_med.cui)
        if persistent_med.cui == None: 
            persistentmeds.append(persistent_med)
            continue
        if len(persistent_med.cui)==0:
            starttime = time.time()
            finish = False
            retries = 0
            max_retries = 5
            while (finish==False)&(retries<max_retries):
                try:
                    dosage, admin, common_name, cui = drugmatch.rxGetDrugProperties(persistent_med.name,mfgID)
                    finish = True
                except Exception as msg:
                    print("An error occurred in drugmatch: %s"%msg)
                    retries += 1
                    pass
            if retries == max_retries:
                print("SUPER ERROR: Hit max retries.")
                return False, hashMe
            if time.time()-starttime<1:
                time.sleep(time.time()-starttime)
            persistent_med.dosage = dosage
            persistent_med.admin = admin
            persistent_med.common_name = common_name
            persistent_med.cui = cui
        persistentmeds.append(persistent_med)

    #add everything to sqlalchemy session and commit it
    database.ver_db_session.add(invoice_db)
    database.ver_db_session.add_all(persistentmeds)
    database.ver_db_session.commit() #cross your fingers!
    return True, hashMe

def main(filename, uploaded_name=""):
    try:
        result,hashMe = saveinvoicetodb(filename,uploaded_name)
        if result:
            return "Success",True
        else:
            return "Duplicate invoice in db",False
    except Exception as err:
        print(str(err))
        return "Rejected invoice: error message: %s" % str(err),False

if __name__ == '__main__':
        saveinvoicetodb("invoice.xls")
        print("Done reading all records")
