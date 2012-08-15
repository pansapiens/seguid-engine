# SEGUID Engine

A sequence id to SEGUID mapping database for Google App Engine.

What is a SEGUID ? Look here => http://bioinformatics.anl.gov/seguid/

## Examples:

### Lookup:
    $ curl -i -X GET "http://localhost:8080/seguid/7P65lsNr3DqnqDYPw8AIyhSKSOw"

    HTTP/1.0 200 
    {"result": "success", "7P65lsNr3DqnqDYPw8AIyhSKSOw": ["sp|P82805", "ref|NP_198909.1", "gb|AAL58947.1"]}

    $ curl -i -X GET "http://localhost:8080/seguid/7P65lsNr3DqnqDYPw8AIyhSKSOw,NetfrtErWuBipcsdLZvTy/rTS80"

    HTTP/1.0 200 
    {"NetfrtErWuBipcsdLZvTy/rTS80": ["sp|P14693", "ref|NP_011951.1", "gb|AAB68885.1"], "result": "success", "7P65lsNr3DqnqDYPw8AIyhSKSOw": ["sp|P82805", "ref|NP_198909.1", "gb|AAL58947.1"]}

### Create:
    $ curl -i -X PUT -d "ids=sp|P50110,ref|NP_013776.1" "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 201

### Update:

We can add mappings (but never take them away):

    $ curl -i -X GET "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 200 
 {"X65U9zzmdcFqBX7747SdO38xuok": ["sp|P50110", "ref|NP_013776.1"], "result": "success"}

    $ curl -i -X PUT -d "ids=gb|AAS56315.1" "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 204 

    $ curl -i -X GET "http://localhost:8080/seguid/X65U9zzmdcFqBX7747SdO38xuok"

    HTTP/1.0 200
    {"X65U9zzmdcFqBX7747SdO38xuok": ["sp|P50110", "gb|AAS56315.1", "ref|NP_013776.1"], "result": "success"}
    
## DONE:
* Insert a single seguid:[id_list] mapping, 
  blindly trusting that client correctly calculated hash
* Add addtional ids to a seguid:[id_list] mapping, 
  (also blindly trusting client)
* Retrieve a seguid:[id_list] mapping
* Retrieve multiple seguid:[id_list] mappings in one operation

## TODO:
* Insert multiple seguid:[id_list] mappings at once.
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
