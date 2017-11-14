# ehhapp-formulary2

Code for the new EHHAPP formulary parser/exporter tool. 

## Roles:
* **Brian** - excel export
* **Dan** - import function
* **Ryan** - persistent database

## Work flow: 

input data (invoice) --> formulary (persistent DB and class) --> Excel sheet, Google Docs, EHHAPP markdown

## Usage: 

See `example.py` for how to import the MedicationRecord class from `invoicerecord.py` (the model for this project).

## Tables: 

1. Medications
2. Medication aliases
3. Versioned input/output sets (to allow for rollback)

Readme last updated: 11/14/2017
