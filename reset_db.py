#!/usr/bin/env python

import os, database

filename = "formulary2.db"

try:
    os.remove(filename)
except OSError:
	pass

database.db.create_all()
