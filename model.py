from google.appengine.ext import db

class Seguid(db.Model):
  """A mapping between a SEGUID and a list of sequence identifiers
     from various databases.
  """
  seguid = db.StringProperty()
  ids = db.StringListProperty()
