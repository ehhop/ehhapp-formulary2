#!/usr/bin/env python

import os, database

filename = "formulary.db"

try:
    os.remove(filename)
except OSError:
	pass

database.db.create_all()
