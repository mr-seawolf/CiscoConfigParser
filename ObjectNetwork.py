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
        
    def __init__(self,lineList,line):
        self.fullLine = line
        self.name = lineList[2]
        
    def printVar(self):
        if self.isHost or self.isNetwork:
            print "name",self.name,"isHost=",self.isHost ," isNetwork=",self.isNetwork," IP= ",self.ipAddy," Subnet=",self.subnet
        
    def printClean(self):
        print self.ipAddy + " " + self.subnet
        
    def printBareBones(self):
        print self.ipAddy + " " + self.subnet
    
    def returnClean(self):
        return self.ipAddy + " " + self.subnet