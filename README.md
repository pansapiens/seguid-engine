# seguid-engine

A SEGUID to biological sequence id mapping database for Google App Engine.

A SEGUID is a Base64 encoded hash of a sequence (for more info, see http://bioinformatics.anl.gov/seguid/). Seguid-engine helps map SEGUIDs to all the
other identifiers associated with a biological sequence.

This is still an experiment. It could be that a secondary function of 
seguid-engine is to make money for Google through App Engine quota charges. 
In other words, it is quite likely that this is going to prove to be a 
stupidly expensive datastore when used for any real-world application of 
SEGUID<->ID mapping.

## Examples:

### Lookup:

#### By SEGUID:
    $ curl -i -X GET "http://localhost:8080/seguid/7P65lsNr3DqnqDYPw8AIyhSKSOw"

    HTTP/1.0 200 
    {"result": "success", "7P65lsNr3DqnqDYPw8AIyhSKSOw": ["sp|P82805", "ref|NP_198909.1", "gb|AAL58947.1"]}

    $ curl -i -X GET "http://localhost:8080/seguid/7P65lsNr3DqnqDYPw8AIyhSKSOw,NetfrtErWuBipcsdLZvTy/rTS80"

    HTTP/1.0 200 
    {"NetfrtErWuBipcsdLZvTy/rTS80": ["sp|P14693", "ref|NP_011951.1", "gb|AAB68885.1"], "result": "success", "7P65lsNr3DqnqDYPw8AIyhSKSOw": ["sp|P82805", "ref|NP_198909.1", "gb|AAL58947.1"]}

#### By ID:
    $ curl -i -X GET "http://alhost:8080/id/sp|P50110,ref|NP_013776.1"
    HTTP/1.0 200
    {"sp|P50110": "X65U9zzmdcFqBX7747SdO38xuok", "result": "success", "ref|NP_013776.1": "X65U9zzmdcFqBX7747SdO38xuok"}
    
### Create:

#### Store SEGUID <-> ID mappings using SEGUIDs calculated by the server, using the sequence:

    $  curl -i -H 'content-type:application/json' -d @seguid_post_example.json http://localhost:8080/seguid
        
    HTTP/1.0 201
    {"failed": [], "created": ["6bObRAVfVkQClLJSQYUw1VlQnU0", "LIt5X1VKZ/LF864/+9OlMi54szY"], "updated": [], "result": "success"}
    
    ... where the input file seguid_post_exaple.json contains:
    
    [{"ids": ["sp|P50110", "gb|AAS56315.1"], "seq": "MVKGSVHLWGKDGKASLISV"}, {"ids": ["sp|A2QRI9"], "seq": "MSVQMALPRPQVGLIVPRPQ"}]

#### Store a SEGUID <-> ID mappings using client-side calculated SEGUIDs:
    _TODO_
    _Example of authenticating with curl, saving the cookie, then using it in a request_

### Update:

As per creating SEGUID mappings. We can add additional mappings, 
but never take them away.

### Bulk insertion from a FASTA database:

A tool is provided to insert large numbers of sequences from a FASTA-formatted
sequence file. It can extract IDs from the standard FASTA header used by NCBI
or Uniprot.
    
    $ ./tools/insert_fasta.py --help
    Usage: insert_fasta.py [options]

      Options:
        -h, --help            show this help message and exit
        -u, --uniprot         Input file has Uniprot style FASTA headers.
                              Otherwise NCBI style is assumed
        -s SERVER_URL, --server=SERVER_URL
                              Input file has Uniprot style FASTA headers.
                              Otherwise NCBI style is assumed
        -b BATCH_SIZE, --batch=BATCH_SIZE
                              Number of sequences to insert per request.
                              Lower this value if you get '500: Internal
                              Server Error' due to timeouts.
                  
    $ ./insert_fasta.py -u -s http://localhost:8080 my_uniprot_sequences.fasta


## Benchmarking

Inserting/updating ~ 4000 typical sequences takes ~ 80 seconds 
(~ 200 ms per sequence).

    $ time tools/insert_fasta.py -f -u EcK12.fasta 
    
    # Inserting sequences 0 (6PGL_ECODH) to 500 (RL21_ECODH) 
    # Inserting sequences 500 (RL22_ECODH) to 1000 (B1XEZ6_ECODH) 
    # Inserting sequences 1000 (B1XGJ3_ECODH) to 1500 (B1X9I7_ECODH) 
    # Inserting sequences 1500 (B1X9I8_ECODH) to 2000 (B1XF28_ECODH) 
    # Inserting sequences 2000 (B1XF41_ECODH) to 2500 (B1XGP5_ECODH) 
    # Inserting sequences 2500 (B1XGV7_ECODH) to 3000 (B1XE18_ECODH) 
    # Inserting sequences 3000 (B1XEC7_ECODH) to 3500 (B1XDG2_ECODH) 
    # Inserting sequences 3500 (B1XEE9_ECODH) to 3990 (B1XHB2_ECODH) 
    # Done
    # Created: 177
    # Updated: 3813
    # Failed: 0

    real	1m22.123s
    user	0m0.136s
    sys	0m0.036s

## DONE:
* Add addtional ids to a seguid:[id_list] mapping using POST, 
  (also blindly trusting client)
* Retrieve a seguid:[id_list] mapping
* Retrieve multiple seguid:[id_list] mappings in one operation
* Retrieve SEGUID's based on ID (Thanks to jcao219).
* Insert seguid mappings via FASTA sequence(s). Only accept sane FASTA headers
  that can create good mappings via the commandline tool 
  (Hashes calculated server-side without authentication, calculated 
   client-side with authentication.).
* Insert multiple seguid:[id_list] mappings at once using POST to /seguid/.
   
## TODO:

* Use task queues for bulk insertion.
* Add OpenID / Googe Account authentication to insert operations where 
  the hash is provided by the client. This way we can at least better track
  losers who dirty up the database.
* Javascript calculation of SEGUID hashes.
* Web interface - lookup id mappings by sequence (NO web interface for
  insertion - require scripting/commandline for this for the moment)
* Consider using Base32-SHA1 instead (like Magnet 
  http://en.wikipedia.org/wiki/Magnet_URI_scheme) since this is naturally URL
  and filesystem safe.

## See also ...
A database of hashes for fast sequence ID mapping is by no means novel. 
Other examples include:

* http://dx.doi.org/10.1093/bioinformatics/bti548
* http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3082858/

