'''
Created on June 26, 2015

@author: MrEd
'''

class DeviceObject:
    hostname = 'unknown'
    ntpServers = []
    model = 'unknown'
        
    def __init__(self,line):
        lineSplit = line.split()
                       
        
            
    def addNTPServer(self,ntpServer):
        self.ntpServers.append(ntpServer)
        
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("hostname="+self.hostname+"\n")
        

        
