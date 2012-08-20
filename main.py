import logging
import os
import hashlib
import base64, sha
import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
#import json
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder
from model import *

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

def seq2seguid(seq):
  return base64.b64encode(sha.new(seq).digest()).strip("=")

# TODO: should be allow/require URL-encoded (RFC 4648) SEGUIDs ?
#       in my testing (curl, Chrome) they don't seem necessary
def b64url_to_b64(b64url_encoded_str):
  """
  Convert base64url to base64, as per RFC 4648.
  
  http://tools.ietf.org/html/rfc4648#section-5
  """
  return b64url_encoded_str.replace('-','+').replace('_','/')

class MainPage(webapp2.RequestHandler):
  def get(self):
    template_values = {}

    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class SeguidMapping(webapp2.RequestHandler):
  """
  Handles adding, updating and retrieving SEGUID to sequence id
  mappings.
  """
  def get(self, seguid_str=""):
    """
    Return all sequence id mappings for a list of 
    comma separated SEGUIDs as JSON.
    
      eg. http://seguid-engine.appspot.com/seguid/7P65lsNr3DqnqDYPw8AIyhSKSOw,NetfrtErWuBipcsdLZvTy/rTS80
      
      Returns:
      {"NetfrtErWuBipcsdLZvTy/rTS80": ["sp|P14693", "ref|NP_011951.1", "gb|AAB68885.1"], "result": "success", "7P65lsNr3DqnqDYPw8AIyhSKSOw": ["sp|P82805", "ref|NP_198909.1", "gb|AAL58947.1"]}
          
    
    If a SEGUID in the list doesn't exist, return a mapping to an
    empty list for that SEGUID. If none of the SEGUIDs exist, return 404.
    """
    if (not seguid_str) or \
       (len(seguid_str) > 27 and (',' not in seguid_str)):
      # if we don't get an acceptable query string, fail
      self.response.status = 400 # Bad Request
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"result":"malformed request"}')
      return
    
    # convert a comma separated list of seguids into a Python list
    # or if only one SEGUID is provided, a single item list 
    if len(seguid_str) > 27 and (',' in seguid_str):
      seguids = seguid_str.split(',')
    else:
      seguids = [seguid_str]
    
    out = {'result':'seguids not found'}
    at_least_some_success = False
    seguid_entities = []
    for s in seguids:
      #ids = Seguid.get_by_key_name('seguid:'+s).ids
      se = Seguid.all().filter("seguid =", s).get()
      if se:
        out[s] = se.ids
        out['result'] = 'success'
      else:
        out[s] = []
    
    # async version
    """
    for s in seguids:
      # convert a key_name into a Key so that we can then use
      # async query
      seguid_key = db.Key.from_path(Seguid.kind(), 'seguid:'+s)
      seguid_entities.append(Seguid.get_async(seguid_key))
    # get results from async lookups
    for se in seguid_entities:
      out[s] = se.ids
    """
      
    if out['result'] == 'success':
      # success
      self.response.status = 200
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(out))
      return
    else:
      # fail
      self.response.status = 404 # Not Found
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(out)
      return
  
  def post(self, seguid):
    """
    Adds a mapping between a SEGUID and a set of sequence identifiers.
    
    If the SEGUID already exists in the datastore, we just add any
    sequence id mappings that don't already exist. We never remove mappings.
    """
    # TODO: batch mode if SEGUID isn't specified on the URL
    #       take a set of mappings is provided as a JSON payload
    
    # TODO: create from FASTA sequence and a set of id mappings
    #       return seqguid:[ids] list
    
    id_str = str(self.request.get('ids'))
    new_ids = []
    if id_str:
      try:
        new_ids = id_str.split(',')
      except:
        self.response.status = 400 # Bad Request
        self.response.out.write('')
      
    existing = Seguid.get_by_key_name('seguid:'+seguid)
    if existing:
      existing.ids = list(set(existing.ids + new_ids))
      existing.put()
      self.response.status = 204 # Success, (not returning any content)
      self.response.out.write('')
      return
    else:
      new_seguid = Seguid(seguid=seguid, ids=new_ids, 
                          key_name='seguid:'+seguid)
      new_seguid.put()
      self.response.status = 201 # Success, resource created
      self.response.out.write('')
      return

class IdMapping(webapp2.RequestHandler):
  """
  Takes a comma-separated list of sequence id(s) and returns the matching SEGUID(s).
  """
  def get(self, seq_id):
    """
    Return all SEGUIDS matching a list of comma separated ids as JSON.

      eg. http://seguid-engine.appspot.com/id/gb|AAS56315.1

      Returns:
      {"result": "success", "gb|AAS56315.1": "X65U9zzmdcFqBX7747SdO38xuok"}    
    
    If an id in the list doesn't exist, return a mapping to an
    empty string for that id. If none of the ids exist, return 404.
    """
    if not seq_id:  # the user did not supply an ID
      self.response.status = 400 # Bad request
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"result":"malformed request"}')
      return

    s_ids = seq_id.split(',')
    out = {}
    one_success = False

    for _id in s_ids:
      sl = Seguid.all().filter("ids = ", _id) # '=' also means 'contains'
      sl = sl.get()
      if sl: # only need 1 result
        out[_id] = sl.seguid
        one_success = True
      else:
        out[_id] = '' # no resulting SEGUID found

    self.response.headers['Content-Type'] = 'application/json'
    if one_success:
      out['result'] = 'success'
      self.response.status = 200 # success
    else:
      out['result'] = 'ids not found'
      self.response.status = 404 # not found
    self.response.out.write(simplejson.dumps(out))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/seguid', SeguidMapping),
                               ('/seguid/(.*)', SeguidMapping),
                               ('/id/(.*)', IdMapping)],
                              debug=True)
