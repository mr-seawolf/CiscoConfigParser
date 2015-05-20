'''
Created on Apr 6, 2014

@author: MrEd
'''

class CryptoMapObject:
    '''
    classdocs
    '''
    name = 'unknown'
    peer = 'unknown'
    matchAddressACL = 'unknown'
    priority = 0


    def __init__(self,line):
        lineSplit = line.split()
        self.name = lineSplit[2]
        
        
    def setPeer(self,peer):
        self.peer = peer
    
    def setMatchAddressACL(self,matchAddressACL):
        self.peer = matchAddressACL
        
    def setPriority(self,priority):
        self.priority = priority
        
    def printVar(self):
        print "name="+self.name+" peer="+str(self.peer)+" matchAddressACL="+str(self.matchAddressACL)+" priority="+str(self.priority)
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("name="+self.name+" peer="+str(self.peer)+" matchAddressACL="+str(self.matchAddressACL)+" priority="+str(self.priority)+"\n")
        

    
       
    
        