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

def check_seguid_sane(seguid):
  """
  Returns True if the provided SEGUID string appears valid.
  """
  if len(seguid) == 27:
    return True
  else:
    return False

def seguid_to_key(seguid):
  """
  Takes a SEGUID string and returns an App Engine datastore key
  suitable for retrieving the associated Seguid entity using db.get().
  eg:
  
    my_seguid = 'X65U9zzmdcFqBX7747SdO38xuok'
    seguid_entity = db.get(seguid_to_key(my_seguid))
  """
  return db.Key.from_path(Seguid.kind(), 'seguid:'+seguid)

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
    
    #################################################################
    # Retrieve SEGUID entities
    #
    # There are three implementations here:
    # 
    # 1. a normal query not using the key or key_name
    # 2. a get by a list of keys in one operation
    # 3. a set of get_async requests, by key
    #
    # It would be interesting to benchmark each approach, and maybe
    # a few others, with different sized requests.
    #
    
    """
    # 1. non-async query of seguid entities
    out = {'result':'seguids not found'}
    seguid_entities = []
    for s in seguids:
      se = Seguid.all().filter("seguid =", s).get()
      if se:
        out[s] = se.ids
        out['result'] = 'success'
      else:
        out[s] = []
    """
    
    """
    # 2. non-async, single-get operation
    out = {'result':'seguids not found'}
    seguid_entities = []
    skeys = []
    for s in seguids:
      skeys.append(db.Key.from_path(Seguid.kind(), 'seguid:'+s))
    # grab every Seguid by key in a single get operation
    seguid_entities = db.get(skeys)
    for se in seguid_entities:
      if se:
        out[s] = se.ids
        out['result'] = 'success'
      else:
        out[s] = []
    """
    
    # 3. async get seguids by key
    out = {'result':'seguids not found'}
    seguid_entities = []
    for s in seguids:
      # convert a key_name into a Key so that we can then use
      # async query
      seguid_key = db.Key.from_path(Seguid.kind(), 'seguid:'+s)
      seguid_entities.append(db.get_async(seguid_key))
    # get results from async lookups
    for se in seguid_entities:
      se = se.get_result()
      if se:
        out[s] = se.ids
        out['result'] = 'success'
      else:
        out[s] = []
    
    #
    #################################################################
      
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
  
  def post(self):
    """
    Adds a mapping between a SEGUID and a set of sequence identifiers.
    Takes a JSON string as the POST body like:
      [{'ids':['sp|P50110', 'gb|AAS56315.1'], 
         'seq': 'MVKGSVHLWGKDGKASLISV'},
       {'ids':['sp|A2QRI9'], 'seq': 'MSVQMALPRPQVGLIVPRPQ'},
      ]
      
    or if client-side SEGUIDs have been provided:
      [{'ids':['sp|P50110', 'gb|AAS56315.1'], 
        'seguid': 'X65U9zzmdcFqBX7747SdO38xuok'},
       {'ids':['sp|A2QRI9'], 'seguid': 'zgyRbn7/VaM2v7GxQ5VGiSoBZX8'},
      ]
    
    Only authenticated users can provide client-side calculated SEGUIDs.
    
    If the SEGUID already exists in the datastore, we just add any
    sequence id mappings that don't already exist. We never remove mappings.
    """
    
    jreq = simplejson.loads(self.request.body)
    
    creation_ops = []
    update_ops = []
    unchanged_list = []
    for i in jreq:
      if 'ids' in i:
        ids = i['ids']
      else:
        self.response.status = 400 # Bad request
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write('{"result":"malformed request"}')
        
      if 'seq' in i:
        seq = i['seq']
        seguid = seq2seguid(seq)
      else:
        self.response.status = 400 # Bad request
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write('{"result":"malformed request"}')
                
      existing = db.get(seguid_to_key(seguid))
      if existing:
        new_id_list = list(set(existing.ids + ids))
        # only do the put operation if new ids are being
        # added, skip it if the update would be pointless
        if len(existing.ids) != len(new_id_list):
          existing.ids = list(set(existing.ids + ids))
          update_ops.append( (seguid, db.put_async(existing)) )
        else:
          unchanged_list.append(seguid)
      else:
        new_seguid = Seguid(seguid=seguid, ids=ids, 
                            key_name='seguid:'+seguid)
        creation_ops.append( (seguid, db.put_async(new_seguid)) )
    
    failed_list = []
    created_list = []
    for seguid, put_future in creation_ops:
      try:
        put_future.check_success()
        created_list.append(seguid)
      except:
        failed_list.append(seguid)
    
    updated_list = []
    for seguid, put_future in update_ops:
      try:
        put_future.check_success()
        updated_list.append(seguid)
      except:
        failed_list.append(seguid)
        
    out = {'created':created_list, 
           'updated':updated_list,
           'unchanged':unchanged_list,
           'failed':failed_list}

    if (created_list or updated_list or unchanged_list) and not failed_list:
      # complete success
      out['result'] = 'success'
      self.response.status = 201 # Success, resource created
      self.response.out.write(simplejson.dumps(out))
      return
    elif (created_list or updated_list or unchanged_list) and failed_list:
      # partial success
      out['result'] = 'partial success'
      self.response.status = 202 # Accepted (but incomplete)
      self.response.out.write(simplejson.dumps(out))
      return
    else:
      # miserable failure
      out['result'] = 'fail'
      self.response.status = 500 # Internal Server Error
      self.response.out.write(simplejson.dumps(out))
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
