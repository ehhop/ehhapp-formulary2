#!/usr/bin/env python

'''
database.py

This is the database model and convenient helper functions
for the persistent FormularyDB for EHHOP. 

Made by Ryan Neff 11/21/17

This hasn't been tested yet...
'''

from invoicerecord import MedicationRecord #import the class definition 
from flask_sqlalchemy import * #import sql wrapper functions from Flask web helper lib
from __init__ import app #import init params like where the db is
from history_meta import versioned_session #make a versioned db so we can rollback stuff

db = SQLAlchemy(app) #create the db object in sqlalchemy
ver_db_session = versioned_session(db.session) #wrap the db in version control

#copypasta from https://stackoverflow.com/questions/6587879/how-to-elegantly-check-the-existence-of-an-object-instance-variable-and-simultan
def get_or_create(model, **kwargs):
	'''checks to see if an object with those properties exists in the db
	   and returns it if it exists, otherwise returns a new object
	   instantiated with the search **kwargs
	'''
    try:
        # basically check the obj from the db, this syntax might be wrong
        object = ver_db_session.query(model).filter(**kwargs).first()
        assert object != None #check if we got an object back
        return object, True #if we did, set found = True
    except AssertionError:
        object = model(**kwargs) #return a blank object instatiated with kwargs if not found
        return object, False #set found to false

class InvoiceRecord(db.Model):
	__tablename__="InvoiceRecord"
	
	id = db.Column(db.BigInteger, primary_key=True)
	medication_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id'))
	#TODO for the rest of it

class PersistentMedication(db.Model):
	'''a persistent record in the database that represents a medication record'''
	__tablename__='PersistentMedication'

	id = db.Column(db.BigInteger, primary_key=True)
	pricetable_id = db.Column(db.Integer) #this is the ID on the invoice, the DB has it's own
	name = db.Column(db.String(255))
	common_name = db.Column(db.String(255))
	dosage = db.Column(db.String(255))
	admin = db.Column(db.String(255))
	prescribeable = db.Column(db.Boolean)
	aliases = db.relationship("MedicationAlias", backref='medication', lazy='dynamic',
	                        cascade="all, delete-orphan") #has many aliases
	history = db.relationship("MedicationHistory", backref='medication', lazy='dynamic',
	                        cascade="all, delete-orphan") # has many histories
	category_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id')) #has one category

	@classmethod #this means that a new PersistentMedication record is loaded into cls
	def from_class(cls,record):
		'''loads the db object from the shared MedicationRecord object
				inputs: record (class MedicationRecord)
		'''
		cls.pricetable_id = record.id
		cls.name = record.name
		cls.common_name = record.common_name
		cls.dosage = record.dosage
		cls.admin = record.admin
		cls.prescribeable = record.prescribeable
		cls.history = [MedicationHistory(medication_id=cls.id,
										 date=record.transactions[i][1],
										 price=record.price[i][1],
										 quantity = record.qty_issued[i][1])
						for i in record.transactions.keys]
		cls.category, _ = get_or_create(Category,name=record.category)
		cls.aliases = [MedicationAlias(medication_id=cls.id,
									  name=alias) for alias in record.aliases]
		return cls #make sure to return the object we just made

	def to_class(self,record=MedicationRecord()):
		'''returns a MedicationRecord class object from the db representation'''
		record.id = self.pricetable_id
		record.name = self.name
		record.common_name = self.common_name
		record.dosage = self.dosage
		record.admin = self.admin
		record.prescribeable = self.prescribeable
		record.transactions = {ix:h.date for ix,h in enumerate(self.history)}
		record.price = {ix:h.price for ix,h in enumerate(self.history)}
		record.qty_issued = {ix:h.quantity for ix,h in enumerate(self.history)}
		record.category = self.category.name
		record.aliases = [alias.name for alias in self.aliases]
		return record #make sure to return the object we just made

	@classmethod #this means that a new PersistentMedication record is loaded into cls
	def create_or_update(cls,record,ver_db_session=ver_db_session):
		'''checks if a MedicationRecord exists in the db and updates the history accordingly if so'''
		match_record,found = get_or_create(cls,pricetable_id=record.id)
		if found:
			if match_record.name != record.name:
				match_record.aliases.append( #checks if the name has changed and adds it as an alias
					get_or_create(MedicationAlias,medication_id=match_record.id,name=record.name)[0])
			match_record.history.append(
							[MedicationHistory(medication_id=match_record.id,
							 date=record.transactions[i][1],
							 price=record.price[i][1],
							 quantity = record.qty_issued[i][1])
						for i in record.transactions.keys]
						) #right now, only update the history of the persistent object with this function
			ver_db_session.add(match_record) #add this to the db session
			ver_db_session.commit()
			return match_record
		else:
			db_record = PersistentMedication.from_class(record)
			ver_db_session.add(db_record) #add this to the db session
			ver_db_session.commit()
			return db_record

	def __repr__(self):
		'''a string representation of the db object'''
		return '<PersistentMed %r, invoice_id: %r, Name:%r>' % (self.id,self.pricetable_id,self.name)

class MedicationAlias(db.Model):
	'''other names for medications in the database that can be used for mathcing'''
	__tablename__='MedicationAlias'

	id = db.Column(db.BigInteger, primary_key=True)
	medication_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id', 
	                           ondelete="CASCADE")) #belongs to 
	name = db.Column(db.String(255))

class MedicationHistory(db.Model):
	'''a record of a transaction of a medication from 
	   an invoice including the price and qty
	   that it was purchased at on a given day/time of 
	   a month
	'''
	__tablename__='MedicationHistory'

	id = db.Column(db.BigInteger, primary_key=True)
	medication_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id', 
	                           ondelete="CASCADE")) #belongs to 
	date = db.Column(db.Time)
	price = db.Column(db.Float)
	quantity = db.Column(db.Integer)

class Category(db.Model):
	'''the category a type of medication belongs to'''
	__tablename__='Category'

	id = db.Column(db.BigInteger, primary_key=True)
	name = db.Column(db.String(255))
	medications = db.relationship("PersistentMedication", #has many medications
		backref='category', lazy='dynamic')

def save_persistent_record(record,ver_db_session=ver_db_session):
	'''saves a MedicationRecord object in the db (just an alias)'''
	return PersistentMedication.create_or_update(record)
