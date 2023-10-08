# models.py

from peewee import *
from app import db

class LibraryEntry(Model):
    libraryaccession = TextField(primary_key=True, index=True)
    libraryname = TextField(index=True)
    libraryjson = BlobField()
    librarysource = TextField(index=True) # e.g. GNPS, Massbank, etc.

    # Last Update Time
    lastupdate = DateTimeField()

    class Meta:
        database = db
