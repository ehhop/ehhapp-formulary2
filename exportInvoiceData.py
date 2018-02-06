#!/usr/bin/env python
'''
Description: outputs desired quantity and cost data in .xlsx format
Inputs: persistant database with medicine list information
Output: excel file in desired format in .xlsx format
11/28/17 Brian Cho
'''

import pandas as pd
import collections
import database as medListDB
import numpy as np
import datetime

def exportrecord(filename, initDateRange = datetime.datetime(1, 1, 1, 0, 0), finalDateRange = datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)):
	def bucketAndQuantify(inputTransactionsList):
		# Input: a list of transactions per MedicationRecord and date range
		# TODO: Default values for range,

		# Buckets by month and calculate issued amount and cost
		# Output: a bucketted list of issued amount and cost per month and total year (month "0")

		# Bucket by months into defaultdict
		# Contain price and quantity information for all transactions each month
		transactionDict = collections.defaultdict(list)
		for tempTransaction in inputTransactionsList:
			if(tempTransaction.date > initDateRange and tempTransaction.date < finalDateRange):
				transactionDict[tempTransaction.date.month].append([tempTransaction.price, tempTransaction.qty])
		# Calculate issue and price per month and year total
		issueCostList = []
		totalScripts = 0
		totalIssue = 0
		totalCost = 0
		yearlyPriceList = []
		for month in transactionDict.keys():
			monthylScripts = 0
			monthlyIssue = 0
			monthlyCost = 0
			monthlyPriceList = []
			for tempTransaction in transactionDict[month]:
				monthlyIssue += tempTransaction[1]
				monthlyCost += tempTransaction[0] * tempTransaction[1]
				monthlyPriceList.append(tempTransaction[0])
				yearlyPriceList.append(tempTransaction[0])
			# Determine number of scripts written each month
			monthylScripts = len(transactionDict[month])
			# Average prices for monthly price
			averageMonthlyPrice = np.mean(monthlyPriceList)
			issueCostList.append([month, monthylScripts, monthlyIssue, monthlyCost, averageMonthlyPrice])
			# Keep running tally for final yearly tabulation
			totalScripts += monthylScripts
			totalIssue += monthlyIssue
			totalCost += monthlyCost
		# Return 0 if no prices recorded
		# if len(yearlyPriceList == 0):
		if not yearlyPriceList:
			averageYearlyPrice = 0
		else:
			averageYearlyPrice = np.mean(yearlyPriceList)
		issueCostList.append([0, totalScripts, totalIssue, totalCost, averageYearlyPrice])
		return issueCostList

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
		# transactionHistoryData.append(i.transactions)

	## Initialize dataframe for holding med info metadata
	medInfoColumns = [[""], ["Name", "Category"]]
	medInfoColumnsList = pd.MultiIndex.from_product(medInfoColumns)
	medInfoDataFrame = pd.DataFrame(data = medInfoData, index = indexList, columns = medInfoColumnsList)

	## Initialize dataframe for holding issue and cost data
	# Use multi-indexing to generate issueCostDataFrame column names
	issueCostColumns = [["Year", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], ["Scripts", "Issue", "Cost", "Price"]]
	issueCostColumnsList = pd.MultiIndex.from_product(issueCostColumns)
	# Initialize dataframe containing 0's
	issueCostDataFrame = pd.DataFrame(data = [[0]*len(issueCostColumns[0])*len(issueCostColumns[1]) for _ in range(len(indexList))], index = indexList, columns = issueCostColumnsList)

	# Populate issueCostDataFrame
	buckettedTransactionHistory = []

	for record in medsList:
		# Extract month, quantity, and cost information only if it exists
		if len(record.transactions) > 0:
			# Bucket and calculate amount of quantity and price per month
			buckettedTransactionHistory = bucketAndQuantify(record.transactions)
			# Populate dataframe with bucketted information
			for monthData in buckettedTransactionHistory:
				issueCostDataFrame.loc[record.id, issueCostColumns[0][monthData[0]]] = [monthData[1], monthData[2], monthData[3], monthData[4]]

	# Combine medInfoDataFrame and issueCostDataFrame for output
	outputDataFrame = pd.concat([medInfoDataFrame, issueCostDataFrame], axis = 1)
	outputDataFrame.index.name = "Item No"

	# Output dataframes into desired format
	# Can't seem to get rid of the extra line in the header for some reason

	# Sort alphabetically by name
	outputDataFrame = outputDataFrame.sort_values(by = [("", "Name")])
	writer = pd.ExcelWriter("downloads/"+filename)
	outputDataFrame.to_excel(writer)
	writer.save()
	return None

if __name__ == '__main__':
    fileName = "internalFormularyCosts.xlsx"
    exportrecord(fileName)
    print("done. file is at downloads/"+fileName)

# Test to see if categories are correctly assigned
# writer = pd.ExcelWriter("test.xlsx")
# medInfoDataFrame.to_excel(writer)
# writer.save()
