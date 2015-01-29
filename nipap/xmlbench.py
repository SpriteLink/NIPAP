#!/usr/bin/env python

from twisted.web.xmlrpc import Proxy
from twisted.internet import reactor
import sys
import datetime
class Request():
    def __init__(self, url, method, params):
        self.url = url
        self.method = method
        self.params = params
        self.start_time = 0
        self.end_time = 0
        self.value =  ""
        self.error = ""
        self.finished = False
        self.error_file = open('errors.csv','w+')


    def addCallback(self, callback):
        self.callback = callback


    def addErrback(self, errback):
        self.errback = errback


    def makeRequest(self):
        proxy = Proxy(self.url)
        proxy.callRemote(self.method,*self.params).addCallbacks(self.retSuccess, self.retFail)
        self.start_time = datetime.datetime.now()


    def __returned(self):
        self.end_time = datetime.datetime.now()


    def retSuccess(self, value):
        self.__returned()
        self.finished = True
        self.value = value
        self.callback(self,value)


    def retFail(self, error):
        self.__returned()
        self.finished = True
        self.error = error
        self.error_file.write("Error: %s" % error)
        self.callback(self,error)


    def isFinished(self):
        return self.finished


    def getTime(self):
        return (self.end_time - self.start_time) # this should be a timedelta


class Benchmark():
    def __init__(self, concurrent = 10, total = 100, url = 'http://localhost:7080/XMLRPC', method = 'date', params=None):
        if params is None:
            params = {}
        self.url = url
        self.method = method
        self.params = params
        self.concurrent_reqs = concurrent
        self.total_reqs = total
        self.open_reqs = 0
        self.current_reqs = 0
        self.error_file = open('errors.csv','w+')
        self.req_times_file = open('times.csv','w+')


    def makeLog(self, filename):
        self.log_file = open(filename,'w+')


    def makeRequest(self):
        req = Request(self.url, self.method, self.params)
        req.addCallback(self.reqSuccess)
        req.addErrback(self.reqError)
        req.makeRequest()
        self.open_reqs = self.open_reqs + 1


    def printReqDetail(self, req):
        #print "Request time: %d ms" % req.getTime().microseconds
        delta = req.getTime()
        print delta


    def reqFinished(self, req):
        self.printReqDetail(req)
        self.open_reqs = self.open_reqs - 1
        self.current_reqs = self.current_reqs + 1 # completed requests
        if ((self.current_reqs + self.open_reqs) < self.total_reqs):
            self.makeRequest()
        else:
            if self.open_reqs == 0:
                reactor.stop() # made as many requests as we wanted to


    def reqSuccess(self,req,value):
        self.reqFinished(req)
        print repr(value)


    def reqError(self,req, error):
        self.reqFinished(req)
        #print 'error', error


    def setupReqs(self):
        for i in range(0,self.concurrent_reqs): # make the initial pool of requests
            self.makeRequest()


if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', dest='port', type='int', default='1337', help="TCP port")
    parser.add_option('-U', '--user')
    parser.add_option('-P', '--password')
    parser.add_option('--concurrent', type='int', default=10, help="Concurrent requests")
    parser.add_option('--total', type='int', default=100, help="Total number of requests")
    parser.add_option('--method', help="XML-RPC method to benchmark")
    parser.add_option('--args', help="Args to XML-RPC method")

    (options, args) = parser.parse_args()

    cred = ''
    if options.user and options.password:
        cred = options.user + ':' + options.password + '@'
    server_url = 'http://%(cred)s127.0.0.1:%(port)d/XMLRPC' % { 'port': options.port, 'cred': cred }

    ad = { 'authoritative_source': 'nipap' }
    args = [{ 'auth': ad, 'message': 'test', 'sleep': 0.1 }]
    args = [{ 'auth': ad, 'query_string': 'foo' }]
    b = Benchmark(concurrent = options.concurrent, total = options.total, url =
            server_url, method = options.method, params = args)
    b.setupReqs()
    reactor.run()
