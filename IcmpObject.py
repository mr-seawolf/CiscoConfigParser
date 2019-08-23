'''
Created on Jul 8, 2013

@author: murphyj
'''
class IcmpObject:
    icmpType = 'unknown'
    fullLine = 'unknown'   
        
    def __init__(self,lineList,line):
        self.fullLine = line
        self.icmpType = lineList[1]
        
          
    def printVar(self):
        print("ICMP Object ",self.icmpType)
        
    def printClean(self):
        buildString = 'icmp-object'
        if self.icmpType != 'unknown':
            buildString = buildString + ' ' + self.icmpType
        print(buildString)
        
    def returnClean(self):
        buildString = ''
        if self.icmpType != 'unknown':
            buildString = buildString + ' ' + self.icmpType
        return buildString
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("icmpType="+self.icmpType+"\n")