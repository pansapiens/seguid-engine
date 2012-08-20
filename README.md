# SEGUID Engine

A SEGUID to sequence id mapping database for Google App Engine.

What is a SEGUID ? Look here => http://bioinformatics.anl.gov/seguid/

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

    TODO

#### Store a SEGUID <-> ID mappings using client-side calculated SEGUIDs:
    $ curl -i -X POST -d "ids=sp|P50110,ref|NP_013776.1" "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 201

### Update:

We can add mappings (but never take them away):

    $ curl -i -X GET "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 200 
 {"X65U9zzmdcFqBX7747SdO38xuok": ["sp|P50110", "ref|NP_013776.1"], "result": "success"}

    $ curl -i -X POST -d "ids=gb|AAS56315.1" "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 204 

    $ curl -i -X GET "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 200
    {"X65U9zzmdcFqBX7747SdO38xuok": ["sp|P50110", "gb|AAS56315.1", "ref|NP_013776.1"], "result": "success"}
    
## DONE:
* Insert a single seguid:[id_list] mapping using PUT, 
  blindly trusting that client correctly calculated hash
* Add addtional ids to a seguid:[id_list] mapping using PUT, 
  (also blindly trusting client)
* Retrieve a seguid:[id_list] mapping
* Retrieve multiple seguid:[id_list] mappings in one operation
* Retrieve SEGUID's based on ID (Thanks to jcao219).

## TODO:
* Insert multiple seguid:[id_list] mappings at once using POST to /seguid/.
* Insert seguid mappings via FASTA sequence(s). Only accept sane FASTA headers
  that can create good mappings via the commandline tool 
  (Hashes calculated server-side without authentication, calculated 
   client-side with authentication. Limit daily anonymous insertions).
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

