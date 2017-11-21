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
import pandas as pd

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
