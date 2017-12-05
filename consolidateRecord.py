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
import pandas as pd

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

        for key, value in data.items():
            print(value)

    #Generate PersistntMedication Record for each item, and add to database
if __name__ == '__main__':
    readrecord("invoice.xls")
    print("done")
