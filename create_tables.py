from app import db
import models
import sys

db.create_tables([models.LibraryEntry], safe=True)