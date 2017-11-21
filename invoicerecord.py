#!/usr/bin/env python

'''
want to import this function

eg. import 'invoicerecord.py' - test danc

'''

import datetime, collections

class MedicationRecord():

	def __init__(self,data):
		self.id = int()
		self.name = str()
		self.common_name = str() #Acetaminophen = Tylenol
		self.price = defaultdict(dict) #{int:float()}
		self.qty_issued = defaultdict(dict) #{int:float()}
		self.transactions = defaultdict(dict) #{int:datetime()}
		self.dosage = str()
		self.admin = str()
		self.category = str() #class of drug
		self.prescribeable = bool()
		self.aliases = list([]) #different names
