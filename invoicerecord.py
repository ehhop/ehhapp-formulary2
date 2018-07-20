#!/usr/bin/env python

'''
want to import this function

eg. import 'invoicerecord.py' - test danc

'''

import datetime, collections, json

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return {'__datetime__': o.replace(microsecond=0).isoformat()}
        return {'__{}__'.format(o.__class__.__name__): o.__dict__}

class MedicationRecord(object):

	class transaction(object):
		date = datetime.time()
		price = float()
		qty = float()
		originInvoiceHash = str()
		def __init__(self, date=None, price=None, qty=None, source=None, originInvoiceHash=None):
			self.date = date if date else datetime.time()
			self.price = price if price else float()
			self.qty = qty if qty else float()
			self.source = source if source else str()
			self.originInvoiceHash = originInvoiceHash

	def __init__(self, pricetable_id=None, name=None, common_name=None,transactions=None,
		dosage=None, admin=None, category=None, prescribable=None, aliases=None, cui=None):
		self.id = pricetable_id if pricetable_id else int() #pricetable id - the item ID from the invoice
		self.name = name if name else str()
		self.common_name = common_name if common_name else str() #Acetaminophen = Tylenol
		self.transactions = transactions if transactions else list([]) #[(class transaction(date,price,qty))]
		self.dosage = dosage if dosage else str()
		self.admin = admin if admin else str()
		self.category = category if category else str() #class of drug
		self.prescribable = prescribable if prescribable else bool()
		self.aliases = aliases if aliases else list([]) #different names
		self.cui = cui if cui else str()

	def __hash__(self):
		return hash(self.id)

	def __eq__(self,other):
		return self.id == other.id

	def __ne__(self,other):
		return not self.__eq__(other)

	def __cmp__(self,other):
		if self.name < other.name:
			return -1
		elif self.name > other.name:
			return 1
		else:
			return 0
