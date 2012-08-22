#!/usr/bin/env python

tally = {}

def FastaHeader2Dic(s, uniprot_style=False):
    """Convert NCBI or Uniprot sequence descriptors to a dictionary of db:accession pairs.
 
     eg: Uniprot
     "sp|B1X797|6PGL_ECODH 6-phosphogluconolactonase" -> {'sp':'B1X797', 'mnemonic':'6PGL_ECODH'}
     
     eg: NCBI
     "gi|50908635|ref|XP_465806.1|" -> {'gi':'50908635', 'ref':'XP_465806.1'}
     
    """
    tok = s.split('|')[:-1]
    tok.reverse()
    dic = {}
    while tok:
        try:
            db = tok.pop()
            acc = tok.pop()
        except:
            break
        dic[db] = acc
    if uniprot_style:
      acc = s.split('|')[-1:][0].split()[0]
      dic['mnemonic'] = acc
    return dic

def insert_seqlist(batch, start=0, end=0):
  sys.stderr.write("# Inserting sequences %i (%s) to %i (%s) \n" % \
                    (start, \
                     batch[0]['ids'][0], \
                     end, \
                     batch[-1:][0]['ids'][0]) )
  req = urllib2.Request(server_url+'/seguid', 
                        json.dumps(batch), headers)

  resp = json.loads(urllib2.urlopen(req).read())
  
  tally['created'] += len(resp['created'])
  tally['updated'] += len(resp['updated'])
  tally['failed'] += len(resp['failed'])
    
  return resp

if __name__ == "__main__":
  import sys, time, urllib2, json
  from optparse import OptionParser
  
  parser = OptionParser(usage = "usage: %prog [options] sequences.fasta")
  parser.add_option("-u", "--uniprot", action="store_true", 
                    dest="uniprot_fasta", default=False,
                    help="Input file has Uniprot style FASTA headers. \
                          Otherwise NCBI style is assumed")
  parser.add_option("-s", "--server", 
                    dest="server_url", 
                    default="http://seguid-engine.appspot.com",
                    help="Input file has Uniprot style FASTA headers. \
                          Otherwise NCBI style is assumed")
  parser.add_option("-b", "--batch", 
                    dest="batch_size", type="int", default=500,
                    help="Number of sequences to insert per request. \
                          Lower this value if you get '500: Internal \
                          Server Error' due to timeouts.")
  parser.add_option("-f", "--failed", 
                    dest="list_failed", action="store_true", default=False,
                    help="List SEGUIDs that failed to insert.")
                         
  (options, args) = parser.parse_args()
  
  if len(args) != 1:
    parser.print_help()
    sys.exit()
  
  server_url = options.server_url
  
  # parse fasta, interpret headers
  seqs_to_send = []
  seqids = None
  seq = ""
  for l in open(args[0]):
    if l.startswith(">"):
      if seqids:
        seqs_to_send.append({'seq':seq, 'ids':seqids.values()})
      seq = ""
      seqids = FastaHeader2Dic(l[1:], uniprot_style=options.uniprot_fasta)
      continue
      
    seq += l.strip()
  seqs_to_send.append({'seq':seq, 'ids':seqids.values()})
    
  #print seqs_to_send
  #print json.dumps(seqs_to_send)
  
    
  # package up sequence and ids as json
  # send the whole lot to the server in batches
  headers = {'Content-Type': 'application/json'}
  tally = {'created':0, 'updated':0, 'failed':0}
  failed = []
  start = 0
  for end in range(options.batch_size, len(seqs_to_send), options.batch_size):

    batch = seqs_to_send[start:end]
    try:
      resp = insert_seqlist(batch, start, end)
    except urllib2.HTTPError:
      time.sleep(5.0)
      sys.stderr.write("# Insert failed, retrying ..\n")
      resp = insert_seqlist(batch, start, end)
      
    if resp['failed']:
      failed.append(resp['failed'])
      
    start = end
    
  end = len(seqs_to_send)
  batch = seqs_to_send[start:end+1]
  try:
    resp = insert_seqlist(batch, start, end)
  except urllib2.HTTPError:
    time.sleep(5.0)
    sys.stderr.write("# Insert failed, retrying ..\n")
    resp = insert_seqlist(batch)
  
  sys.stderr.write("# Done\n")
  
  if options.list_failed and failed:
    sys.stderr.write("# Failed to insert: \n")
    sys.stderr.write(`failed`+'\n')
    
  sys.stderr.write("# Created: %i\n# Updated: %i\n# Failed: %i\n" % \
                   (tally['created'], 
                    tally['updated'], 
                    tally['failed']) )
  #print urllib2.urlopen(req).read()
  
