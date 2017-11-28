#!/usr/bin/env python

'''
want to import this function

eg. import 'invoicerecord.py' - test danc

'''

import datetime, collections

class MedicationRecord(object):
	
	id = int() #pricetable id - the item ID from the invoice
	name = str()
	common_name = str() #Acetaminophen = Tylenol
	transactions = list([]) #[(class transaction(date,price,qty))]
	dosage = str()
	admin = str()
	category = str() #class of drug
	prescribable = bool()
	aliases = list([]) #different names
	
	class transaction():
		date = datetime.time()
		price = float()
		qty = float()

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)

	def __repr__(self):
		return "<MedicationRecord, id=%d, common_name=%s>" % (self.id, self.common_name)