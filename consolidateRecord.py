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
    invoice_db, is_imported = database.get_or_create(database.Invoice,checksum=hash_file(file))
    if is_imported:
        return False
    invoice_db.filename=file
    invoice_db.date_added = datetime.datetime.now()
    database.ver_db_session.add(invoice_db)
    database.ver_db_session.commit()
    for ix,row in ds.iterrows():
        newobj = database.InvoiceRecord(invoice_id=invoice_db.id)
        for df_col in ds.columns:
            col = invoice_columns[actualcolumns.index(df_col)]
            setattr(newobj,col,str(row[df_col]))
            #print(col,getattr(newobj,col))
        #break
        invoiceobjs.append(newobj)
    database.ver_db_session.add_all(invoiceobjs)
    database.ver_db_session.commit()
    return True


def readrecord(file):
    ds = pd.read_excel(file,usecols=range(0,17))
    ds = ds.dropna(axis=0,thresh=len(ds.columns)-3)
    ds = ds[[col for col in actualcolumns if col in ds.columns]]
    data = dict()
    for ix,row in ds.iterrows():
        pricetable_id = int(row["Item No"])           #Medication ID

        if numpy.isnan(pricetable_id):
            continue
        
        medication_name = row["Item Description"]         #Medicaction Name
        qty = int(row["Issue Qty"])             #Quantity of Medication issued
        price = float(row["Extended Price"])/qty       #Medication price
        date_issued = row["Requisition Date"]
        category = row["Comdty Name "] if "Comdty Name " in row else ""
        date_issued = date_issued.to_pydatetime()

        #Insantiate a new Medication record
        record = MedicationRecord(pricetable_id = pricetable_id, \
            name = medication_name, category=category,\
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
