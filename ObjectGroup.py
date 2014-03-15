'''
Created on Jul 2, 2013

@author: MrEd
'''

class ObjectGroup:
    fullLine = 'unknown'
    listOfNetworkObjects = []
    listOfServiceObjects = []
    listOfObjectGroups = []
    listOfIcmpObjects = []
    listOfPortObjects = []
    listOfProtocolObjects =[]
    description = 'unknown'
    typeOfObjectGroup = 'unknown'
    name = 'unknown'
    typeOfServiceGroup = 'unknown'
    
    def __init__(self,lineList,line):
        self.fullLine = line
        self.typeOfObjectGroup = lineList[1]
        self.name = lineList[2]
        self.listOfNetworkObjects = []
        self.listOfServiceObjects = []
        self.listOfObjectGroups = []
        self.listOfIcmpObjects = []
        self.listOfPortObjects = []
        self.listOfProtocolObjects = []
        self.description = 'unknown'
        self.typeOfServiceGroup = 'unknown'
        if lineList[1] == 'service' and len(lineList) == 4:
            self.typeOfServiceGroup = lineList[3]
        
    def printVar(self):
        if self.typeOfServiceGroup == 'service':
            print self.name + " " + self.typeOfServiceGroup
        else:
            print self.name + " " + self.description
        for x in self.listOfNetworkObjects:
            x.printClean()
        for x in self.listOfServiceObjects:
            x.printVar()
        for x in self.listOfIcmpObjects:
            x.printVar()
        for x in self.listOfPortObjects:
            x.printVar()
        for x in self.listOfProtocolObjects:
            x.printVar()
        for x in self.listOfObjectGroups:
            print x
        #for x in self.listOfObjectGroups:
        #    x.printVar()
    
    def printClean(self):
        if self.typeOfServiceGroup == 'service':
            print self.name + " " + self.typeOfServiceGroup
        else:
            print self.name + " " + self.description
        for x in self.listOfNetworkObjects:
            x.printClean()
        for x in self.listOfServiceObjects:
            x.printClean()
        for x in self.listOfIcmpObjects:
            x.printClean()
        for x in self.listOfPortObjects:
            x.printClean()
        for x in self.listOfProtocolObjects:
            x.printClean()
        for x in self.listOfObjectGroups:
            print x
    
    def printDirectItemsOnly(self):
        for x in self.listOfNetworkObjects:
            x.printClean()
        for x in self.listOfServiceObjects:
            x.printClean()
        for x in self.listOfIcmpObjects:
            x.printClean()
        for x in self.listOfPortObjects:
            x.printClean()
        for x in self.listOfProtocolObjects:
            x.printClean()
    
    def returnClean(self):
        returnList = []
        for x in self.listOfNetworkObjects:
            returnList.append(x.returnClean())
        for x in self.listOfServiceObjects:
            returnList.append(x.returnClean())
        for x in self.listOfIcmpObjects:
            returnList.append(x.returnClean())    
        for x in self.listOfPortObjects:
            returnList.append(x.returnClean())
        for x in self.listOfProtocolObjects:
            returnList.append(x.returnClean())    
        return returnList
        
    def returnProtocolAttributes(self):
        returnList = []
        for x in self.listOfServiceObjects:
            returnList.append(x.returnProtocolAttributes())
        return returnList
    
    def returnDestPorts(self):
        returnList =[]
        for x in self.listOfServiceObjects:
            returnList.append(x.returnDestPorts())
        return returnList
    
    
    def printListCounts(self):
        print self.name," NetworkObjects= ",len(self.listOfNetworkObjects), " ServiceObjects= ",len(self.listOfServiceObjects),\
        " PortObjects= ",len(self.listOfPortObjects)," ICMP= ",len(self.listOfIcmpObjects)," Proto= ",len(self.listOfProtocolObjects)
        
    def writeToDebugLogDirectItemsOnly(self,outputFileDebugDump): 
        if self.typeOfServiceGroup == 'service':
            outputFileDebugDump.write("name="+self.name+" typeOfServiceGroup="+self.typeOfServiceGroup+"\n")
        else:
            outputFileDebugDump.write("name= "+self.name+" description="+self.description+"\n")
        for x in self.listOfNetworkObjects:
            outputFileDebugDump.write("   ")
            x.writeToDebugLog(outputFileDebugDump)
        for x in self.listOfServiceObjects:
            outputFileDebugDump.write("   ")
            x.writeToDebugLog(outputFileDebugDump)
        for x in self.listOfIcmpObjects:
            outputFileDebugDump.write("   ")
            x.writeToDebugLog(outputFileDebugDump)
        for x in self.listOfPortObjects:
            outputFileDebugDump.write("   ")
            x.writeToDebugLog(outputFileDebugDump)
        for x in self.listOfProtocolObjects:
            outputFileDebugDump.write("   ")
            x.writeToDebugLog(outputFileDebugDump)
        for x in self.listOfObjectGroups:
            outputFileDebugDump.write("   ")
            outputFileDebugDump.write("nameOfGroup= "+ x + "\n")
        
        
                