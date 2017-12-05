#!/usr/bin/env python

'''
want to import this function

eg. import 'invoicerecord.py' - test danc

'''

import datetime, collections

class MedicationRecord(object):

	pricetable_id = int() #pricetable id - the item ID from the invoice
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
		def __init__(self, date,price,qty):
			self.date = date
			self.price = price
			self.qty = qty

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)

	def __hash__(self):
		return hash(self.pricetable_id)

	def __eq__(self,other):
		return self.pricetable_id == other.pricetable_id

	def __ne__(self,other):
		return not self.__eq__(other)

	def __cmp__(self,other):
		if self.name < other.name:
			return -1
		elif self.name > other.name:
			return 1
		else:
			return 0



	def __repr__(self):
		return "<MedicationRecord, id=%d, name=%s, entries=%d>" % (self.pricetable_id, self.name, len(self.transactions))
