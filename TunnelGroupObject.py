'''
Created on Apr 6, 2014

@author: MrEd
'''

class TunnelGroupObject:
    '''
    classdocs
    '''
    peer = 'unknown'
    type = 'unknown'
    groupPolicy = 'unknown'

    def __init__(self,line):
        lineSplit = line.split()
        self.peer = lineSplit[1]
        if lineSplit[2] == 'type':
            self.type = lineSplit[3]

    def setGroupPolicy(self,groupPolicy):
        self.groupPolicy = groupPolicy
        
    def printVar(self):
        print("peer="+self.peer+" type="+str(self.type)+" groupPolicy="+str(self.groupPolicy))
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("peer="+self.peer+" type="+str(self.type)+" groupPolicy="+str(self.groupPolicy)+"\n")
        

  
    
    