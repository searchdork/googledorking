This tool consists of four main components:
(1) /opt/googledorking/etc/googledorking.cfg
(2) runGoogleDorking.py
(3) queries.txt
(4) completed_queries.txt

Command information is logged to syslog.  Results are pushed to a path specified in the config file.  The default path to the config is /opt/googledorking/etc/googledorking.cfg.  This can be changed by modifying the appropriate line in the runGoogleDorking.py script.

------------------ 
Config File:
------------------ 
The config file has the below structure

[custom-search]
api-key = (this is your search API key, there are many like it but this one is yours)
custom-search-id = (same as they key, use this to designate sites in scope)

[query-options]
max_per_run = 99 (this is the maximum queries per run - if you are using the free quota I recommend setting this value between 90 and 100 and running the tool a max of once per day)
max_results = 100 (this is the number of results in a result set you request. 100 is max google provides)

[google-search-options]
basedomain = www.googleapis.com (don't mess with these)
basepath = /customsearch/v1? (don't mess with these)
safe = off (do you want to find potentially adult content)

[dorking]
queryfile=/etc/googledorking/queries.txt (location of file where list of queries resides)
completedqueryfile=/opt/googledorking/completed_queries.txt (location of file where completed queries are stored)

[output]
resultsfile=/opt/googledorking/%Y-%m/googledorking-%Y%m%d_%H%M%S.txt (output file for finding - use strftime format for timestamped files - tool will generate directory structure if it does not exist)
delimiter=\t (delimiter in standard string markup form)



------------------ 
runGoogleDorking.py
------------------ 
This script handles parsing the query strings from the supplied file and requesting their result sets from the Google custom search API.  The configuration for per run behavior can be handled as detailed above in the config.

This script has been enhanced so it can save the state of the search progress and will execute all of the queries listed in the queries file before cycling back to the beginning of the list.  It is somewhat robust in that it will accomodate changes to the queries file into the search list.

Known bugs:
 * Finishing the query list does not cycle back to the beginning that run and would require re-lauch to finish using quota.
 * Running out of searches (403) may not correctly save state.
 * Full result sets (default 100) will not be pulled if max number of queries per day is reached.  Next run will start on next query.



------------------ 
queries.txt
------------------ 
Google search strin file with the format of
<QuerySourceName>;;<Category or Descriptor>;;<Search String>

Stach & Liu have a nice collection of hacking queries hosted on their site and bundled with their tool Search Diggity
http://www.stachliu.com/resources/tools/google-hacking-diggity-project/attack-tools/

For a more complete set of queries (and one that is constantly updated) visit Exploit Database:
http://www.exploit-db.com/google-dorks/


------------------
completed_queries.txt
------------------
Same structure as above - this acts as a state file for the purposes of splitting searches across multiple runs.


