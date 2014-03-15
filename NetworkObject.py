'''
Created on Jun 29, 2013

@author: MrEd


'''
class NetworkObject:
    isHost = False
    isNetwork = False
    ipAddy = "0.0.0.0"
    subnet = "255.255.255.255"
    fullLine = 'unknown'
    name = 'unknown'
        
    def __init__(self,typeOfObject,lineList,line):
        ruleSplit = line.split()
                
        if ruleSplit[0] == 'network-object':
            self.parseLine(typeOfObject,lineList,line)
        elif ruleSplit[1] == 'network': 
            self.name = ruleSplit[2]
    
    def parseLine(self,typeOfObject,lineList,line):
        self.typeOfObject = typeOfObject 
        self.fullLine = line
        if typeOfObject == 'network host':
            self.isHost = True
            self.ipAddy = lineList[1]
        
        if typeOfObject == 'host':
            self.isHost = True
            self.ipAddy = lineList[2]
        if typeOfObject == 'network':
            self.isNetwork = True
            self.ipAddy = lineList[1]
            self.subnet = lineList[2]
    def printVar(self):
        print "isHost=",self.isHost ," isNetwork=",self.isNetwork," IP= ",self.ipAddy," Subnet=",self.subnet
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("name="+self.name+" isHost="+str(self.isHost)+" isNetwork="+str(self.isNetwork)+" IP="+self.ipAddy+" Subnet="+self.subnet+"\n")
        
    def printClean(self):
        print self.ipAddy + " " + self.subnet
        
    def printBareBones(self):
        print self.ipAddy + " " + self.subnet
    
    def returnClean(self):
        return self.ipAddy + " " + self.subnet
        
        
