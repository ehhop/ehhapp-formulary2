#!/usr/bin/env python

'''
database.py

This is the database model and convenient helper functions
for the persistent FormularyDB for EHHOP.
'''

from invoicerecord import MedicationRecord #import the class definition
from flask_sqlalchemy import * #import sql wrapper functions from Flask web helper lib
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin #used for logins (not yet activated)
import datetime
from __init__ import app #import init params like where the db is
from sqlalchemy import orm, asc, desc #this is used to give SQLite properties to our Python classes
import json #used in Invoice.properties

db = SQLAlchemy(app) #create the db object in sqlalchemy
ver_db_session = db.session #we wated to do version control at some point, oops...

def get_all_medication_records():
    '''get_all_medication_records()

    Description: gets all medication records as class MedicationRecord from the database.
    This is an abstraction layer that is useful for the views and interoperability.

    Inputs:
        None

    Returns:
        A list() of class MedicationRecord objects as defined in invoicerecord.py.

    Example:
        import database
        med_record_list = database.get_all_medication_records()
        ## returns [list of MedicationRecord() objects] ##
    '''
    return [i.to_class() for i in PersistentMedication.query.all()]

def save_persistent_record(record,ver_db_session=ver_db_session, commit=True):
    '''save_persistent_record()
    Description: 
        Saves a MedicationRecord object in the db (abstraction layer)

    Usage: 
        medrecord = MedicationRecord(id=12345,...)
        save_persistent_record(medrecord)
    '''
    return PersistentMedication.create_or_update(record, commit=commit)

#copypasta from https://stackoverflow.com/questions/6587879/how-to-elegantly-check-the-existence-of-an-object-instance-variable-and-simultan
def get_or_create(model, **kwargs):
    '''get_or_create()

    Description: checks to see if an object with those properties exists in the db
    and returns it if it exists, otherwise returns a new object
    instantiated with the search **kwargs

    Inputs:
        model
            an empty instance of a class that inherits from sqlalchemy.model (e.g. class PersistentMedication(db.Model)).
            This should work with any class in this file.
        **kwargs
            filters for the database on that model when checking if an object exists already.
            For example, if we pass pricetable_id=12345 in the keyword arguments,
            it will return the first item of class *model* from the database that
            matches pricetable_id=12345 (e.g. the first PersistentMedication record).

    Returns:
        object
            The class object that was either found from the database or instantiated with **kwargs.
            This always returns an object the same class as the input *model*.
        found
            A boolean that denotes whether we found an object in the database (GET) or are
            instantiating it (CREATE). True if GET, False if CREATE.
    '''
    try:
        object = ver_db_session.query(model).filter_by(**kwargs).first() #check if the object of class model exists in db
                                                                        #filtered on kwargs criteria and return the first match
        assert object != None #check if we got an object back
        return object, True #if we did, set found = True
    except AssertionError:
        object = model(**kwargs) #return a blank object instatiated with kwargs if not found
        return object, False #set found to false

class Invoice(db.Model):
    '''class Invoice(db.Model)

    Description: Holds a record that corresponds to the invoice FILE.
    Each file has many InvoiceRecords (lines/rows) associated with it.

    Usage: Invoice.query.get(1) returns the Invoice object with id=1.
    '''

    __tablename__="Invoice" # the table in the sqlite file this class refers to

    id = db.Column(db.Integer, primary_key=True,autoincrement=True) #column in DB: an autoincrementing number that labels this invoice and used by the DB for matching
    filename = db.Column(db.String(255)) #column in DB: string
    date_added = db.Column(db.DateTime) #column in DB: datetime
    checksum = db.Column(db.String(255)) #column in DB: string
    properties = db.Column(db.Text) #column in DB: TEXT (stores unstructured info about the invoice
                                    #  from a Python dict as JSON (in case we want to add some sort of special tag to this invoice)
    records = db.relationship("InvoiceRecord", backref='invoice', lazy='dynamic',
                        cascade="all, delete-orphan")
                        # NOT A COLUMN - this is a SQL join that
                        #   matches between Invoice.id <-> InvoiceRecord.invoice_id.
                        #   Invoice has one or many InvoiceRecords.
                        #   InvoiceRecord belongs to Invoice.
                        # This gets populated so that Invoice.records is an object that
                        #   cointains all InvoiceRecords that are linked to this invoice (forward join).
                        # backref='invoice' means that if you do InvoiceRecord.invoice,
                        #   you will get an Invoice object (reverse join).
                        # cascade="all, delete-orphan" means that when the Invoice object is deleted,
                        #   all InvoiceRecords with InvoiceRecord.invoice_id==Invoice.id are deleted too!
                        # lazy='dynamic' means that Invoice.records will be a SQLAlchemy query() rather than
                        #   an array of InvoiceRecord objects (you need to run e.g. Invoice.query.get(1).records.all()
                        #   to retrieve them for invoice) to speed up this return value.

    def properties_dict(self):
        '''function that parses the properties column (text) to a Python dict.

        Usage: Invoice.query.get(1).properties_dict()
        '''
        return json.loads(str(self.properties).replace("'","\""))

class InvoiceRecord(db.Model):
    '''class InvoiceRecord(db.Model)

    Description: Holds lines of an invoice. The columns in this DB are designed to mirror
        those found in the actual invoices. We do this so that we don't lose any info.

    '''
    __tablename__="InvoiceRecord" # the table in the sqlite file this class refers to

    id = db.Column(db.Integer, primary_key=True,autoincrement=True) #column in db: autoincrementing ID used by the db internally (for joins, etc)
    medication_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id')) #column in db: holds a PersistentMedication.id (foreign key for SQL joins)
    history_obj = db.relationship("MedicationHistory", backref='invoicerecord', lazy='dynamic',
                        cascade="all, delete-orphan")
                         # NOT A COLUMN - this is a SQL join that
                         #   matches between InvoiceRecord.id <-> MedicationHistory.invoice_record_id.
                         #   InvoiceRecord has one MedicationHistory.
                         #   MedicationHistory belongs to InvoiceRecord.
                         # This gets populated so that InvoiceRecord.history_obj is an object that
                         #   cointains the MedicationHistory that are linked to this InvoiceRecord (forward join).
                         # backref='invoicerecord' means that if you do MedicationHistory.invoicerecord,
                         #   you will get an InvoiceRecord object (reverse join).
                         # cascade="all, delete-orphan" means that when the InvoiceRecord object is deleted,
                         #   all MedicationHistory with MedicationHistory.invoice_record_id==InvoiceRecord.id are deleted too!
                         # lazy='dynamic' means that InvoiceRecord.history_obj will be a SQLAlchemy query() rather than
                         #   an array of MedicationHistory objects (you need to run e.g. InvoiceRecord.query.get(1).history_obj.all()
                         #   to retrieve them for invoicerecord) to speed up this return value.
    invoice_id = db.Column(db.BigInteger, db.ForeignKey('Invoice.id')) #column in DB: holds an Invoice.id (foreign key for SQL joins)
    exp_code = db.Column(db.String(255)) #column in db
    supply_loc = db.Column(db.String(255)) #column in db
    item_no = db.Column(db.String(255)) #column in db
    item_description = db.Column(db.String(255)) #column in db
    vendor_name = db.Column(db.String(255)) #column in db
    vendor_ctg_no = db.Column(db.String(255)) #column in db
    mfr_name = db.Column(db.String(255)) #column in db
    mfr_ctlg_no = db.Column(db.String(255)) #column in db
    comdty_name = db.Column(db.String(255)) #column in db
    comdty_code = db.Column(db.String(255)) #column in db
    requisition_no = db.Column(db.String(255)) #column in db
    requisition_date = db.Column(db.String(255)) #column in db
    issue_qty = db.Column(db.String(255)) #column in db
    um = db.Column(db.String(255)) #column in db
    price = db.Column(db.String(255)) #column in db
    extended_price = db.Column(db.String(255)) #column in db
    cost_center_no = db.Column(db.String(255)) #column in db

    #InvoiceRecord.invoice is a backref on this object, so this also exists for this class.


class PersistentMedication(db.Model):
    '''class PersistentMedication(db.Model)

    Description: A persistent record in the database that represents a medication record.
        This is different than invoicerecord.py's MedicationRecord object.
    '''
    __tablename__='PersistentMedication' #table in the sqlite file this class refers to

    id = db.Column(db.Integer, primary_key=True,autoincrement=True) #column in DB, autoincrementing and autopopulated by DB
    pricetable_id = db.Column(db.Integer) #this is the ID we use to match a line from the invoice file to a persistent medication, should not change for that med
    name = db.Column(db.String(255)) #column in db - the name of the med we get the first time we instantiate the object
    common_name = db.Column(db.String(255)) #col in db - the colloquial name of the med
    dosage = db.Column(db.String(255)) # col in db
    admin = db.Column(db.String(255)) # col in db
    cui = db.Column(db.String(255)) # col in db - this is the drug match identifier (only filled after drug matching)
    prescribable = db.Column(db.Boolean) # col in db - boolean that lets us know whether or not the drug can be prescribed (set in UI)
    aliases = db.relationship("MedicationAlias", backref='medication', lazy='dynamic',
                        cascade="all, delete-orphan")
                        # NOT A COLUMN - this is a SQL join that
                        #   matches between PersistentMedication.id <-> MedicationAlias.medication_id.
                        #   PersistentMedication has one or many MedicationAlias.
                        #   MedicationAlias belongs to PersistentMedication.
                        # This gets populated so that PersistentMedication.aliases is an object that
                        #   cointains all MedicationAlias that are linked to this PersistentMedication (forward join).
                        # backref='medication' means that if you do MedicationAlias.medication,
                        #   you will get a PersistentMedication object (reverse join).
                        # cascade="all, delete-orphan" means that when the PersistentMedication object is deleted,
                        #   all MedicationAlias with PersistentMedication.id==MedicationAlias.medication_id are deleted too!
                        # lazy='dynamic' means that PersistentMedication.aliases will be a SQLAlchemy query() rather than
                        #   an array of MedicationAlias objects (you need to run e.g. PersistentMedication.query.get(1).aliases.all()
                        #   to retrieve them for PersistentMedication) to speed up this return value.
    history = db.relationship("MedicationHistory", backref='medication', lazy='dynamic',
                        cascade="all, delete-orphan")
                        # NOT A COLUMN - this is a SQL join that
                        #   matches between PersistentMedication.id <-> MedicationHistory.medication_id.
                        #   PersistentMedication has one or many MedicationHistory.
                        #   MedicationHistory belongs to PersistentMedication.
                        # This gets populated so that PersistentMedication.history is an object that
                        #   cointains all MedicationHistory that are linked to this PersistentMedication (forward join).
                        # backref='medication' means that if you do MedicationHistory.medication,
                        #   you will get a PersistentMedication object (reverse join).
                        # cascade="all, delete-orphan" means that when the PersistentMedication object is deleted,
                        #   all MedicationHistory with PersistentMedication.id==MedicationHistory.medication_id are deleted too!
                        # lazy='dynamic' means that PersistentMedication.history will be a SQLAlchemy query() rather than
                        #   an array of MedicationHistory objects (you need to run e.g. PersistentMedication.query.get(1).history.all()
                        #   to retrieve them for PersistentMedication) to speed up this return value.
    category_id = db.Column(db.BigInteger, db.ForeignKey('Category.id')) #column in db: holds a Category.id (foreign key for SQL joins)
    #we also have a backref here: PersistentMedication.category (not shown)

    def __init__(self, **kwargs): # this initializes PersistentMedication with whatever **kwargs you give it (hacky but it works)
        self.__dict__.update(kwargs)

    @staticmethod
    def from_class(record):
        '''Usage: loads the db object from the shared MedicationRecord object
                inputs: record (class MedicationRecord)
                outputs: PersistentMedication
           Example: 
            medrecord = MedicationRecord(id=12345,...)
            persistentmed = PersistentMedication.from_class(medrecord)
        '''
        init_db = PersistentMedication() #creates a new persistentmed object
        init_db.pricetable_id = record.id #populates the persistentmed object with medicationrecord values...
        init_db.name = record.name
        init_db.common_name = record.common_name
        init_db.dosage = record.dosage
        init_db.admin = record.admin
        init_db.prescribable = record.prescribable
        init_db.cui = record.cui
        init_db.history = [MedicationHistory(medication_id=init_db.id,
                                         date=i.date,
                                         price=i.price,
                                         quantity = i.qty,
                                         origin = i.originInvoiceHash)
                        for i in record.transactions] #makes new MedicationHistory objects in db that correspond to MedicationRecord.transaction objects
        init_db.category, _ = get_or_create(Category,name=record.category) #create or assign an existing category to the medication by name
        init_db.aliases = [MedicationAlias(medication_id=init_db.id,
                                      name=alias) for alias in record.aliases] # makes new MedicationAlias objects in db that correspond to 
									       # MedicationRecord.aliases
        return init_db #make sure to return the PersistentMedication object we just made so we can commit it

    def to_class(self):
        '''Usage: returns a MedicationRecord class object from the db representation
                Inputs: PersistentMedication
                Outputs: MedicationRecord

        Example: 
            persistentmed = PersistentMedication.query.get(1)
            medrecord = persistentmed.to_class()
        '''
        record = MedicationRecord() #make a new medicationRecord object
        record.id = self.pricetable_id
        record.name = self.name
        record.common_name = self.common_name
        record.dosage = self.dosage
        record.admin = self.admin
        record.prescribable = self.prescribable
        record.cui = self.cui
        record.transactions = [MedicationRecord.transaction(date=h.date,
                                    price=h.price,
                                    qty=h.quantity) for h in self.history.order_by(asc(MedicationHistory.date))] #populate MedicationRecord.transactions
														 #from PersistentMedication.history
        record.category = self.category.name 
        record.aliases = [alias.name for alias in self.aliases] #populate MedicationRecord.aliases from PersistentMedication.aliases
        return record #make sure to return the object we just made

    @classmethod #this means that a new PersistentMedication record is loaded (so you don't have to)
    def create_or_update(cls,record,ver_db_session=ver_db_session, commit=True):
        '''Usage: checks if a PersistentMedication exists for the passed MedicationRecord object in the db and 
        updates the history accordingly if so.

        Example: persistentmed = PersistentMedication.create_or_update(MedicationRecord)

        Think of MedicationRecords as objects that this function is filtering into a set of PersistentMedication buckets.
        Aliases are extra names from the invoices for the same medication,
        Histories are transactions you made where you bought/sold that med,
        etc.
        '''
        match_record,found = get_or_create(cls,pricetable_id=record.id) #see the doc for this function
        if found: # if we have a PersistentMedication bucket
            if match_record.name != record.name:
                match_record.aliases.append( #checks if the name has changed and adds it as an alias if its a new alias else use the existing alias
                    get_or_create(MedicationAlias,medication_id=match_record.id,name=record.name)[0])
            match_record.history.extend( #adds transaction history to our PersistentMedication bucket, iterating through transactions
                        [MedicationHistory(medication_id=match_record.id,
                         date=i.date,
                         price=i.price,
                         quantity = i.qty,
                         origin = i.originInvoiceHash)
                    for i in record.transactions]
                    ) #right now, only update the history of the persistent object with this function
            ver_db_session.add(match_record) #add this to the db session
            if commit: ver_db_session.commit() #commits the record
            return match_record #return the updated persistentmed object
        else: # if we are creating a new bucket
            db_record = PersistentMedication.from_class(record) #instantiate the persistentmed from the medrecord class object
            ver_db_session.add(db_record) #add this to the db session
            if commit: ver_db_session.commit() #commit
            return db_record #return the new persistentmed bucket

class MedicationAlias(db.Model):
    '''

    Description: 
        other names for medications in the database that can be used for mathcing'''
    __tablename__='MedicationAlias' #table in db this corresponds to 

    id = db.Column(db.Integer, primary_key=True,autoincrement=True) #column in db: autoincrementing key (used for SQL joins)
    medication_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id',
                               ondelete="CASCADE")) #column in DB: holds a PersistentMedication.id (foreign key for joining)
    name = db.Column(db.String(255)) #column in db

    #we also have a backref here: MedicationAlias.medication (not shown)

class MedicationHistory(db.Model):
    '''a record of a transaction of a medication from
       an invoice including the price and qty
       that it was purchased at on a given day/time of
       a month
    '''
    __tablename__='MedicationHistory' #table in db this corresponds to

    id = db.Column(db.Integer, primary_key=True,autoincrement=True) #column in db: autoincrementing key (used for SQL joins)
    medication_id = db.Column(db.BigInteger, db.ForeignKey('PersistentMedication.id',
                               ondelete="CASCADE")) #column in db: holds a PersistentMedication.id (foreign key for joining)
    invoice_record_id = db.Column(db.BigInteger, db.ForeignKey('InvoiceRecord.id',ondelete="CASCADE")) #column in DB: holds a Invoiceredord.id (foreign key for joining)
    date = db.Column(db.DateTime) #column in db
    price = db.Column(db.Float) #column in db
    quantity = db.Column(db.Integer) #column in db
    origin = db.Column(db.String(255)) #column in db
    #we also have a backref here: MedicationHistory.invoice_record (not shown)
    #we also have a backref here: MedicationHistory.medication (not shown)

class Category(db.Model):
    '''the category a type of medication belongs to
       because this category corresponds to many meds, 
       we put the category in a separate table to make
       it easy to update the category name
    '''
    __tablename__='Category' #table in db this corresponds to

    id = db.Column(db.Integer, primary_key=True,autoincrement=True) #column in db: autoincrementing key (used for SQL joins)
    name = db.Column(db.String(255)) #column in db
    medications = db.relationship("PersistentMedication", backref="category",lazy="dynamic")
                        # NOT A COLUMN - this is a SQL join that
                        #   matches between PersistentMedication.category_id <-> Category.id.
                        #   PersistentMedication belongs to a Category.
                        #   Category has many PersistentMedications.
                        # This gets populated so that Category.medications is an object that
                        #   cointains all PersistentMedications that are linked to this Category (forward join).
                        # backref='category' means that if you do PersistentMedication.category,
                        #   you will get a Category object (reverse join).
                        # lazy='dynamic' means that Category.medications will be a SQLAlchemy query() rather than
                        #   an array of PersistentMedication objects (you need to run e.g. Category.query.get(1).medications.all()
                        #   to retrieve them for Category) to speed up this return value.

class User(db.Model, UserMixin):
    '''class User(db.Model, UserMixin)

    Description: Not used right now, but will be once we enable Mount Sinai Google-OAuth2 logins.
    Used by flask to check if a user is logged in or not, stores session cookies and emails,
    names, avatars, session_tokens, etc.

    TODO:
        need to add standard Flask functions for logging in, out, as
        shown in https://github.com/ehhop/ehhapp-twilio/blob/master/ehhapp_twilio/models.py
    '''

    __tablename__ = "user" # the table in the sqlite file this class refers to

    email = db.Column(db.String(100), unique=True, nullable=False,primary_key=True) #user's email
    name = db.Column(db.String(100), nullable=True) #user's real name
    avatar = db.Column(db.String(200)) #this is going to be a URL for a gravatar??
    tokens = db.Column(db.Text) #this is where the Google OAuth2 token will be saved
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow()) #when the user first logs in, this is autoset

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False
