'''
Created on Jul 6, 2013

@author: MurphyJ
'''
class ProtocolObject:
    protocol = 'unknown'
    fullLine = 'unknown'   
        
    def __init__(self,lineList,line):
        self.fullLine = line
        self.protocol = lineList[1]
        
          
    def printVar(self):
        print("Protocol Object ",self.protocol)
        
    def printClean(self):
        buildString = 'protocol-object'
        if self.protocol != 'unknown':
            buildString = buildString + ' ' + self.protocol
        print(buildString)
        
    def returnClean(self):
        buildString = ''
        if self.protocol != 'unknown':
            buildString = buildString + ' ' + self.protocol
        return buildString
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("protocol="+self.protocol+"\n")