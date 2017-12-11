#!/usr/bin/env python

import os, database

filename = "formulary2.db"

try:
    os.remove(filename)
except OSError as e: # this would be "except OSError, e:" before Python 2.6
	if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
		raise # re-raise exception if a different error occurred

database.db.create_all()