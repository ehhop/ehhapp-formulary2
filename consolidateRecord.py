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

def saveinvoicetodb(file):
    invoice_columns = ['medication_id', #column titles to use
                     'invoice_id',
                     'exp_code',
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

    ds = pd.read_excel(file, header = 0,skiprows = 3,names=invoice_columns)
    invoiceobjs = []
    invoice_db = database.Invoice(filename=file,date_added = datetime.datetime.now())
    database.ver_db_session.add(invoice_db)
    for ix,row in ds.iterrows():
        newobj = database.InvoiceRecord(invoice_id=invoice_db.id)
        for col in invoice_columns:
            setattr(newobj,col,row[col])
        invoiceobjs.append(newobj)
    database.ver_db_session.add_all(invoiceobjs)
    database.ver_db_session.commit()
    return "Completed."


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
if __name__ == '__main__':
    readrecord("invoice.xls")
    print("done")
