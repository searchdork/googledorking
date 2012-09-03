#!/usr/bin/python
import json, urllib
import syslog, ConfigParser
import httplib, datetime
import os

# modify this line if you have the googledorking config file somewhere else
config_file_path = '/opt/googledorking/etc/googledorking.cfg'

def load_config(config_filename):
    config = ConfigParser.RawConfigParser()
    config.read(config_filename)
    conf={}
    conf["search_key"] = config.get( "custom-search", "api-key")
    conf["search_id"] = config.get( "custom-search", "custom-search-id")
    conf["search_safe"] = config.get( "google-search-options", "safe")
    conf["basedomain"] = config.get( "google-search-options", "basedomain")
    conf["basepath"] = config.get( "google-search-options", "basepath")
    conf["max_per_run"] = config.get( "query-options", "max_per_run")
    conf["max_results"] = config.get( "query-options", "max_results")
    conf["queryfile"] = config.get( "dorking", "queryfile")
    conf["completedqueryfile"] = config.get( "dorking", "completedqueryfile")
    conf["resultsfile"] = config.get( "output", "resultsfile")
    conf["delimiter"] = config.get( "output", "delimiter")
    
    return conf


def load_queries(query_filename):
    queryfile = open(query_filename, 'r')
    queries = []
    for q in queryfile:
        db_catq = q.partition(";;")
        database = db_catq[0]
        cat_q = db_catq[2].partition(";;")
        category = cat_q[0]
        query = cat_q[2].rstrip("\r\n")
        queries.append([database,category,query])
    queryfile.close()
    return queries


def write_complete_queries(queries,filename):
    queryfile = open(filename, 'wb')
    
    for q in queries:
        queryfile.write(q[0] + ";;" + q[1] + ";;" + q[2] + "\n")
    queryfile.close()



def log_results(query, item, delim, resultsfile):
    rout = datetime.datetime.today().strftime("%Y/%m/%d %H:%M:%S")
    rout += delim + query[0] # Query database source
    rout += delim + query[1] # Query category
    rout += delim + query[2] # Query string
    if "title" in item:
        rout += delim + item["title"]
    else:
        rout += delim
    if "link" in item: # actual link
        rout += delim + item["link"]
    else:
        rout += delim
    if "displayLink" in item: # results display link
        rout += delim + item["displayLink"]
    else:
        rout += delim
    if "cacheId" in item: # actual link
        rout += delim + item["cacheId"]
    else:
        rout += delim
    if "snippet" in item: # this should be last in case it has a delim in it
        rout += delim + item["snippet"]
    else:
        rout += delim
    resultsfile.write(rout.encode('utf-8') + "\n")


def main():
    # index_inc is the max step value for api result size
    # don't change this value unless you really know what
    # you are doing
    index_inc = 10
    
    #global counters (leave these alone)
    num_queries = 0
    num_success = 0
    total_results = 0
    
    # load keys and configuration from file
    conf = load_config(config_file_path)

    #open handle to syslog
    syslog.openlog("googledorking")

    #open results file
    routfile = datetime.datetime.today().strftime(conf["resultsfile"])
    d = os.path.dirname(routfile)
    if not os.path.exists(d):
        os.makedirs(d)
    resultsfile = open(routfile, 'wb')

    #load queries
    queries = load_queries(conf["queryfile"])

    completedqueries = ()
    #load completed queries
    if os.path.isfile(conf["completedqueryfile"]):
        completedqueries = load_queries(conf["completedqueryfile"])
    else:
        try:
            open(conf["completedqueryfile"], 'w').close()
        except IOError as e:
            print "I detect foul play"
            exit()
            
        completedqueries = load_queries(conf["completedqueryfile"])

    # write log header
    resultsfile.write("## time,title,link,display_link,cache_id,snippet\n" )

    #remove already completed queries
    for cq in completedqueries:
        for q in queries:
            if q == cq:
                queries.remove(q)
            continue

    #for each query
    for query in queries:
        #assemble GET string
        get_str = conf["basepath"]
        get_str += "cx=" + conf["search_id"]
        get_str += "&key=" + conf["search_key"]
        get_str += "&alt=json"
        get_str += "&num=10"
        get_str += "&q=" + urllib.quote( query[2].replace("\n","") )
        start = 0
        num_results=0

        
        #request results (while under daily quota and number of results)
        while (start > -1 and start <= conf["max_results"] and num_queries < int(conf["max_per_run"])):
            #form connection
            #print conf["basedomain"] , get_str
            conn = httplib.HTTPSConnection(conf["basedomain"])
            if start == 0:
                conn.request("GET", get_str)
            else:
                conn.request("GET", get_str + "&start=" + str(start))
            req = conn.getresponse()
            num_queries+=1
            
            # check for request errors
            #ERROR - unless 200 or 302 stop
            if(req.status == 200 or req.status == 302):
                num_success+=1

                # parse results
                data = json.load(req)
                #print data
                
                # check range then set next start
                if int(data["queries"]["request"][0]["totalResults"]) > start + index_inc:
                    start+=index_inc
                else:
                    # start on next query set
                    start=-1

                # check for results
                if "items" in data:
                    # for each result, print to log file
                    for item in data["items"]:
                        if num_results < conf["max_results"]:
                            log_results(query, item, conf["delimiter"].decode("string-escape"), resultsfile)
                            num_results+=1
                            total_results+=1

	        syslog.syslog("Ran Query[index=" + str(start) + "]: " + str(query))
        	completedqueries.append(query)
           
 
            else:
                syslog.syslog("An error occured accessing the Google API")
                syslog.syslog( str(req.status) + " " + req.reason )
                syslog.syslog( json.load(req)["error"]["message"] )
                syslog.closelog()
                exit()

    #remove already completed queries
    for cq in completedqueries:
        for q in queries:
            if q == cq:
                queries.remove(q)
            continue

    # if all queries have been completed
    # use completed query list as query list
    # and reset completed list
    if len(queries) == 0:
        queries = completedqueries
        completedqueries = []

    # output updated query list for next run
    write_complete_queries(completedqueries,conf["completedqueryfile"])

    #output summary
    syslog.syslog("Successfully ran ( " + str(num_success) + "/" + str(num_queries) + " ) from run max of ( " + str(conf["max_per_run"]) + " )")
    syslog.syslog("Generated ( " + str(total_results) + " ) results")
    syslog.closelog()
    exit()



if __name__ == "__main__":
    main()
