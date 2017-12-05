#!/usr/bin/env python
'''
Description: reads EHHOP formularly invoice in .xls format
Inputs: EHHOP formularly invoice in .xls standard format
Output: Consolidated formulary invoice record with summed issues in .csv format

11/20/2017 Daniel Charytonowicz

'''
import os, collections, invoicerecord, csv
import collections
import invoicerecord
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
            setattr(newobj,col) = row[col]
        invoiceobjs.append(newobj)
    database.ver_db_session.add_all(invoiceobjs)
    database.ver_db_session.commit()
    return "Completed."


def readrecord(file):
    ds = pd.read_excel(file, header = 0,skiprows = 3)
    data = dict()
    for i in range(ds.shape[0]):

        if ds.iloc[i][2] in data:               #If item there, add up issued!
            item = data[ds.iloc[i][2]]
            item[1] = item[1] + float(ds.iloc[i][12])
            data[ds.iloc[i][2]] = item
        else:                                   #If new item, add to record
            data[ds.iloc[i][2]] = [ds.iloc[i][3], float(ds.iloc[i][12]), round(float(ds.iloc[i][14]),2)]

    #Sort the final result
    output = collections.OrderedDict(sorted(data.items(), key=lambda t: t[0]))

    #Output to read_csv
    header = ['Item Number', 'Item Description', "Issue Qty", "Price (USD)"]
    out_file = csv.writer(open("invoice.csv", "wb"))
    out_file.writerow(header)
    for key, value in output.items():
        line = [key] + value
        out_file.writerow(line)

if __name__ == '__main__':
    readrecord("invoice.xls")