'''
Removes all medicationHistory database references with the given

- 1. Delete the Invoice from the invoice table
- 2. Go to PersistantMedicaion and check for what is blank

        db_session.delete(inv).commit()

'''
import database
def undo(invoiceChecksum):
    #check if we  have anything
    query = database.Invoice.query.filter(database.Invoice.checksum.is_(invoiceChecksum)).all()
    #quit if there is no query
    if not query:
        print "no result!"
        return
    #get the proper invoiceId from invocies to delete the invoice record
    invoiceId =  query[0].id

    #delete invoice
    database.Invoice.query.filter(database.Invoice.checksum.is_(invoiceChecksum)).delete()

    #delete the invoicerecord if it matches the invoiceID number from the invoice
    database.InvoiceRecord.query.filter(database.InvoiceRecord.invoice_id.is_(invoiceId)).delete()

    #delete medicationHistory using the invocieChecksum
    database.MedicationHistory.query.filter(database.MedicationHistory.origin.is_(invoiceChecksum)).delete()

    #commit deletions
    database.ver_db_session.commit()

    #delete persistant medication if the ID shown in persistantmedication is not found anywhere in medication history
    persistMeds =  database.PersistentMedication.query.all()
    for persistantMed in persistMeds:
        medId = persistantMed.id
        if (len(database.MedicationHistory.query.filter(database.MedicationHistory.medication_id.is_(medId)).all()) == 0):
            database.PersistentMedication.query.filter(database.PersistentMedication.id.is_(medId)).delete()

    #commit deletions again
    database.ver_db_session.commit()
if __name__ == '__main__':
    undo("2ca8ba9b69e35c0d575cd814a67c9da2e0e06b48")
