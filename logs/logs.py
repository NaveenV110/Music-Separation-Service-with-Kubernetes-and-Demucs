import sys
import redis

##
## Configure test vs. production
##

##
## Configure test vs. production
##

redisClient = redis.StrictRedis(host='redis', port=6379, db=0)

while True:
    try:
        work = redisClient.blpop("logging", timeout=0)
        ##
        ## Work will be a tuple. work[0] is the name of the key from which the data is retrieved
        ## and work[1] will be the text log message. The message content is in raw bytes format
        ## e.g. b'foo' and the decoding it into UTF-* makes it print in a nice manner.
        ##
        print(work[1].decode('utf-8'))
    except Exception as exp:
        print(f"Exception raised in log loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()