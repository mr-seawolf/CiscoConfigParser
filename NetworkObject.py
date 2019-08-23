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
    natSourceInterface = 'unknown'
    natDestInterface = 'unknown'
    natType = 'unknown'
    natTranslation = 'unknown'
    natLineNum = 0
        
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
        print("isHost=",self.isHost ," isNetwork=",self.isNetwork," IP= ",self.ipAddy," Subnet=",self.subnet)
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("name="+self.name+" isHost="+str(self.isHost)+" isNetwork="+str(self.isNetwork)+" IP="+self.ipAddy+" Subnet="+self.subnet+"\n")
        outputFileDebugDump.write("      natType="+self.natType+" natSourceInt="+self.natSourceInterface+" natDestInt="+self.natDestInterface+" natTranslation="+self.natTranslation+"\n")
    def printClean(self):
        print(self.ipAddy + " " + self.subnet)
        
    def printBareBones(self):
        print(self.ipAddy + " " + self.subnet)
    
    def returnClean(self):
        return self.ipAddy + " " + self.subnet
        
        
