#!/usr/bin/env python

'''

eg. import 'invoicerecord.py' - test danc

'''

import datetime, defaultdict

class MedicationRecord():

	def __init__(self,data):
		self.id = int()
		self.name = str()
		self.common_name = str() #Acetaminophen = Tylenol
		self.price = defaultdict({datetime.date():float()})
								#includes history
		self.dosage = str()
		self.admin = str()
		self.category = str() #class of drug
		self.prescribeable = bool()
		self.aliases = list([]) #different names
