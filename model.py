from google.appengine.ext import db

class Seguid(db.Model):
  """A mapping between a SEGUID and a list of sequence identifiers
     from various databases.
     
     Seguid entities must always be created with key_name='seguid:'+seguid .
  """
  seguid = db.StringProperty()
  ids = db.StringListProperty()
