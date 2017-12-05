#!/usr/bin/env python

'''
want to import this function

eg. import 'invoicerecord.py' - test danc

'''

import datetime, collections

class MedicationRecord(object):
	
	class transaction():
		def __init__(self, date=None, price=None, qty=None, source=None):
			self.date = date if date else datetime.time()
			self.price = price if price else float()
			self.qty = qty if qty else float()
			self.source = source if source else str()

	def __init__(self, id=None, name=None, common_name=None,transactions=None,
		dosage=None, admin=None, category=None, prescribable=None, aliases=None):
		self.id = id if id else int() #pricetable id - the item ID from the invoice
		self.name = name if name else str()
		self.common_name = common_name if common_name else str() #Acetaminophen = Tylenol
		self.transactions = transactions if transactions else list([]) #[(class transaction(date,price,qty))]
		self.dosage = dosage if dosage else str()
		self.admin = admin if admin else str()
		self.category = category if category else str() #class of drug
		self.prescribable = prescribable if prescribable else bool()
		self.aliases = aliases if aliases else list([]) #different names

	def __repr__(self):
		return "<MedicationRecord, id=%d, name=%s, common_name=%s>" % (self.id, self.name, self.common_name)