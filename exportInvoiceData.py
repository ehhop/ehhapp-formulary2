#!/usr/bin/env python
'''
Description: outputs desired quantity and cost data in .xlsx format
Inputs: persistant database with medicine list information
Output: excel file in desired format in .xlsx format
11/28/17 Brian Cho
'''

import pandas as pd
import invoicerecord		# is this required?
import database as medListDB

## Assume meds is list of MedicationRecord
medsList = medListDB.get_all_medication_records()	#import meds list from database

## Extract desired data in one loop from medsList
indexList = []
medInfoData = []
transactionHistoryData = []
for i in medsList:
	# Create list of index using id numbers from medsList
	# Will assume unique id nubmers to use as identifiers in database
	indexList.append(i.id)
	# Extract med info metadata
	medInfoData.append([i.name, i.category])
	# Extract transaction history data
	transactionHistoryData.append(i.transactions)

## Initialize dataframe for holding med info metadata
medInfoColumnsList = ["Name", "Category"]
medInfoDataFrame = pd.DataFrame(data = medInfoData, index = indexList, columns = medInfoColumnsList)

## Initialize dataframe for holding issue and cost data
# Use multi-indexing to generate issueCostDataFrame column names
issueCostColumns = [["Year", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], ["Issue", "Cost"]]
issueCostColumnsList = pd.MultiIndex.from_product(issueCostColumns)
# Initialize dataframe containing 0's
issueCostDataFrame = pd.DataFrame(data = [[0]*len(issueCostColumns[0])*len(issueCostColumns[1]) for _ in range(len(indexList))], index = indexList, columns = issueCostColumnsList)

# Populate issueCostDataFrame
for transactionsIndex in range(len(transactionHistoryData)):
	if len(transactionHistoryData[transactionsIndex]) > 0:
		# Extract month, quantity, and cost information
		totalIssue = 0
		totalCost = 0
		for transaction in transactionHistoryData[transactionsIndex]:
			# Question: Is transactions going to be pre-processed to bucket by months?
			# Will assume transactions are bucketed by months for now
			issueCostDataFrame.loc[transactionsIndex, issueCostColumns[0][transaction.date.month]] = [transaction.qty, transaction.qty*transaction.price]
			totalIssue += transaction.qty
			totalCost += transaction.qty*transaction.price
		issueCostDataFrame.loc[transactionsIndex, "Year"] = [totalIssue, totalCost]
	else:
		# Should be pre-populated with 0's

# Output dataframes into desired format
# Can't seem to get rid of the extra line in the header for some reason
writer = pd.ExcelWriter("internalFormularyCosts.xlsx")
issueCostDataFrame.to_excel(writer, startcol=len(medInfoColumnsList))
medInfoDataFrame.to_excel(writer, startrow=2)
writer.save()

