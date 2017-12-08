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

	class transaction():
		def __init__(self, date=None, price=None, qty=None, source=None):
			self.date = date if date else datetime.time()
			self.price = price if price else float()
			self.qty = qty if qty else float()
			self.source = source if source else str()

	def __init__(self, pricetable_id=None, name=None, common_name=None,transactions=None,
		dosage=None, admin=None, category=None, prescribable=None, aliases=None):
		self.pricetable_id = pricetable_id if id else int() #pricetable id - the item ID from the invoice
		self.name = name if name else str()
		self.common_name = common_name if common_name else str() #Acetaminophen = Tylenol
		self.transactions = transactions if transactions else list([]) #[(class transaction(date,price,qty))]
		self.dosage = dosage if dosage else str()
		self.admin = admin if admin else str()
		self.category = category if category else str() #class of drug
		self.prescribable = prescribable if prescribable else bool()
		self.aliases = aliases if aliases else list([]) #different names

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
