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
import datetime
import drugmatch

actualcolumns= ["Exp Code",
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

invoice_columns = ['exp_code',
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
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def saveinvoicetodb(file):
    ds = pd.read_excel(file,usecols=range(0,17))
    ds = ds.dropna(axis=0,thresh=len(ds.columns)-3)
    ds = ds[[col for col in actualcolumns if col in ds.columns]]
    invoiceobjs = []
    hashMe = hash_file(file)
    invoice_db, is_imported = database.get_or_create(database.Invoice,checksum=hashMe)
    if is_imported:
        return False,hashMe
    invoice_db.filename=file
    invoice_db.date_added = datetime.datetime.now()
    for ix,row in ds.iterrows():
        newobj = database.InvoiceRecord(invoice_id=invoice_db.id)
        for df_col in ds.columns:
            col = invoice_columns[actualcolumns.index(df_col)]
            setattr(newobj,col,str(row[df_col]))
            #print(col,getattr(newobj,col))
        #break
        invoice_db.records.append(newobj)

    data = dict()

    originInvoiceHash = hashMe 
    for ix,row in ds.iterrows():
        pricetable_id = int(row["Item No"])           #Medication ID

        if numpy.isnan(pricetable_id):
            continue

        medication_name = row["Item Description"]         #Medicaction Name
        mfgID = row["Mfr Ctlg No"]
        qty = int(row["Issue Qty"])             #Quantity of Medication issued
        price = float(row["Extended Price"])/qty       #Medication price
        date_issued = row["Requisition Date"]
        category = row["Comdty Name "] if "Comdty Name " in row else ""
        date_issued = date_issued.to_pydatetime()

        #Insantiate a new Medication record
        record = MedicationRecord(pricetable_id = pricetable_id, \
            name = medication_name,\
            category=category,\
            transactions = [MedicationRecord.transaction(date = date_issued,price = price,qty = qty,originInvoiceHash = originInvoiceHash)])
        #Check if the record is in database, if not add it
        if record in data:
            #since the record is in the database, update transactions
            old_record = data[record]
            old_record.transactions += record.transactions
        else:
            #Add record to database, only here to query to save time
            dosage, admin, common_name, cui = drugmatch.rxGetDrugProperties(medication_name,mfgID)
            record.dosage = dosage
            record.admin = admin
            record.common_name = common_name
            record.cui = cui
            data[record] = record

    #print("HashOrigin Is:"+str(originInvoiceHash))
    persistentmeds = []
    for key, value in data.items():
        #print value.transactions
        persistentmeds.append(database.save_persistent_record(value, commit=False)) #cross your fingers!
            #print(value)
    database.ver_db_session.add(invoice_db)
    database.ver_db_session.add_all(persistentmeds)
    database.ver_db_session.commit() #cross your fingers!
    return True, hashMe
    #Generate PersistntMedication Record for each item, and add to database

def save_hash_for_invoice(invoice_id):
    try:
        invoice_db = database.Invoice.query.get(invoice_id)
        hashMe = hash_file(invoice_db.filename)
        invoice_db.checksum = hashMe
        database.ver_db_session.add(invoice_db)
        database.ver_db_session.commit()
    except BaseException as msg:
        return "An error occurred: %s" % msg
    return None

def main(filename):
    try:
        result,hashMe = saveinvoicetodb(filename)
        if result:
            return "Success",True
        else:
            return "Duplicate invoice in db",False
    except Exception as err:
        print(str(err))
        return "Rejected invoice: error message: %s" % str(err),False

if __name__ == '__main__':
        saveinvoicetodb("invoice.xls")
        readrecord("invoice.xls")
        print("Done reading all records")
