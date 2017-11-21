import pandas as pd

# Assume meds is list of MedicationRecord
medsList = []	#import meds list

# Determine list of ids to use as index
indexList = []
for i in medsList:
	indexList = indexList.append(i.id)

#Initialize DataFrame for holding data
columnsList = ["Name", "Category", 
				"YearIssue", "YearCost", 
				"JanIssue", "JanCost", 
				"FebIssue", "FebCost", 
				"MarIssue", "MarCost", 
				"AprIssue", "AprCost", 
				"MayIssue", "MayCost", 
				"JunIssue", "JunCost", 
				"JulIssue", "JulCost", 
				"AugIssue", "AugCost", 
				"SepIssue", "SepCost", 
				"OctIssue", "OctCost", 
				"NovIssue", "NovCost", 
				"DecIssue", "DecCost"]
medsDataFrame = pd.DataFrame(index = indexList, columns = columnsList)
medsDataFrame.info()




