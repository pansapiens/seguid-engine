#!/usr/bin/env python
from optparse import OptionParser

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
    
if __name__ == "__main__":
  import sys, urllib2, json
  parser = OptionParser()
  parser.add_option("-u", "--uniprot", action="store_true", 
                    dest="uniprot_fasta", default=False,
                    help="Input file has Uniprot style FASTA headers. \
                          Otherwise NCBI style is assumed")
  parser.add_option("-s", "--server", 
                    dest="server_url", 
                    default="http://seguid-engine.appspot.com",
                    help="Input file has Uniprot style FASTA headers. \
                          Otherwise NCBI style is assumed")
                         
  (options, args) = parser.parse_args()
  
  if options.uniprot_fasta:
    filetype = 'uniprot_fasta'
  else:
    filetype = 'ncbi_fasta'
  
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
      seqids = FastaHeader2Dic(l[1:])
      continue
      
    seq += l.strip()
    
  #print json.dumps(seqs_to_send)
  
  # package up sequence and ids as json
  # send the whole lot to the server
  headers = {'Content-Type': 'application/json'}
  req = urllib2.Request(server_url+'/seguid', 
                        json.dumps(seqs_to_send), headers)
  print urllib2.urlopen(req).read()
  
