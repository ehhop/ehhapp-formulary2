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

    ds = pd.read_excel(file, header = 0,skiprows = 3,usecols=range(0,17),names=invoice_columns).dropna(thresh=3)
    invoiceobjs = []
    invoice_db, is_imported = database.get_or_create(database.Invoice,checksum=hash_file(file))
    if is_imported:
        return False
    invoice_db.filename=file
    invoice_db.date_added = datetime.datetime.now()
    database.ver_db_session.add(invoice_db)
    database.ver_db_session.commit()
    for ix,row in ds.iterrows():
        newobj = database.InvoiceRecord(invoice_id=invoice_db.id)
        for col in invoice_columns:
            setattr(newobj,col,str(row[col]))
            #print(col,getattr(newobj,col))
        #break
        invoiceobjs.append(newobj)
    database.ver_db_session.add_all(invoiceobjs)
    database.ver_db_session.commit()
    return True


def readrecord(file):
    ds = pd.read_excel(file, header = 0,skiprows = 3)
    data = dict()
    for i in range(ds.shape[0]):
        pricetable_id = ds.iloc[i][2]           #Medication ID

        if numpy.isnan(pricetable_id):
            continue

        medication_name = ds.iloc[i][3]         #Medicaction Name
        qty = ds.iloc[i][12]             #Quantity of Medication issued
        price = ds.iloc[i][14]       #Medication price
        date_issued = ds.iloc[i][11]
        date_issued = date_issued.to_pydatetime()

        #Insantiate a new Medication record
        record = MedicationRecord(pricetable_id = pricetable_id, \
            name = medication_name, \
            transactions = [MedicationRecord.transaction(date_issued,price,qty)])
        #Check if the record is in database, if not add it
        if record in data:
            #since the record is in the database, update transactions
            old_record = data[record]
            old_record.transactions += record.transactions
        else:
            data[record] = record

    print(len(data))

    for key, value in data.items():
        database.save_persistent_record(value) #cross your fingers!
            #print(value)

    #Generate PersistntMedication Record for each item, and add to database

def main(filename):
    try:
        result = saveinvoicetodb(filename)
        if result:
            readrecord(filename)
            return "Success",True
        else:
            return "Duplicate invoice in db",False
    except Exception as err:
        print(str(err))
        return "Rejected invoice: error message: %s" % str(err),False

if __name__ == '__main__':
    result = saveinvoicetodb("invoice.xls")
    if result:
        readrecord("invoice.xls")
        print("done reading invoice.")
    else:
        print("invoice already imported. Stop.")
