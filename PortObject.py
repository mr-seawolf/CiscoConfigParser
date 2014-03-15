'''
Created on Jul 3, 2013

@author: MrEd
'''

class PortObject:
    operator = 'unknown'
    port = 'unknown'
    startRange = 'unknown'
    stopRange = 'unknown'
    fullLine = 'unknown'   
        
    def __init__(self,lineList,line):
        self.fullLine = line
        self.operator = lineList[1]
        if self.operator == 'eq' or self.operator == 'gt' or self.operator=='lt' or self.operator=='neq':
                self.port = lineList[2]
        if self.operator == 'range':
                self.startRange = lineList[2]
                self.stopRange = lineList[3]
          
    def printVar(self):
        print "PortObject ",self.operator,self.port,self.startRange,self.stopRange
        
    def printClean(self):
        buildString = 'port-object'
        if self.operator != 'unknown':
            buildString = buildString + ' ' + self.operator
        if self.port != 'unknown':
            buildString = buildString + ' ' + self.port
        if self.startRange != 'unknown':
            buildString = buildString + ' ' + self.startRange
        if self.stopRange != 'unknown':
            buildString = buildString + ' ' + self.stopRange
        print buildString
        
    def returnClean(self):
        buildString = ''
        if self.operator != 'unknown':
            buildString = buildString + ' ' + self.operator
        if self.port != 'unknown':
            buildString = buildString + ' ' + self.port
        if self.startRange != 'unknown':
            buildString = buildString + ' ' + self.startRange
        if self.stopRange != 'unknown':
            buildString = buildString + ' ' + self.stopRange
        return buildString
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("operator="+self.operator+" port="+self.port+" startRange="+self.startRange+" stopRange="+self.stopRange+"\n")
        