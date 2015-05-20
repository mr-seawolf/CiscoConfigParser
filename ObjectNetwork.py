'''
Created on Aug 10, 2013

@author: MrEd

This is created from lines of "object network xxxxx"
Not be confused with network-object objects. Later ASA versions started using "object network"
'''
class ObjectNetwork:
    name = 'unknown'
    isHost = False
    isNetwork = False
    isServiceObject = False
    ipAddy = "0.0.0.0"
    subnet = "255.255.255.255"
    fullLine = 'unknown'
    natSourceInterface = 'unknown'
    natDestInterface = 'unknown'
    natType = 'unknown'
    natTranslation = 'unknown'
    natLineNum = 0
        
    def __init__(self,lineList,line):
        self.fullLine = line
        self.name = lineList[2]
        
    def setNatSourceInterface(self,var1):
        self.natSourceInterface = var1
    def setNatDestInterface(self,var1):
        self.natDestInterface = var1
    def setNatType(self,var1):
        self.natType = var1 
    def setNatTranslation(self,var1):
        self.natTranslation = var1
    def setNatLineNum(self,var1):
        self.natLineNum = var1    
    
    def printVar(self):
        if self.isHost or self.isNetwork:
            print "name",self.name,"isHost=",self.isHost ," isNetwork=",self.isNetwork," IP= ",self.ipAddy," Subnet=",self.subnet
        
    def printClean(self):
        print self.ipAddy + " " + self.subnet
        
    def printBareBones(self):
        print self.ipAddy + " " + self.subnet
    
    def returnClean(self):
        return self.ipAddy + " " + self.subnet