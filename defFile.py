from  NetworkObject import *
from  ServiceObject import *
from  PortObject import *
from  ProtocolObject import *
from  ObjectGroup import *
from  IcmpObject import *
from  AccessList import *
from  AccessGroup import *


#This will return a list[] of a ACL line expanded to every combination. It can be rather large
#list contains entries like: access-list outside_access_in extended permit tcp 192.168.101.0 255.255.255.0 10.150.130.144 255.255.255.255  eq https
def ExpandRule(rule):
    global listOfObjectGroups, tempObjectGroupExpanded
    global listOfAccessLists
    tempExpandedRules = []
    tempExpandedRulesContainsOG = []
    tempExpandedRules2 = []
    
    ruleSplit = rule.split()
    ruleName = ruleSplit[1]
    foundObjectGroup = False
    countUsedObjectGroups = 0
    objectGroupIndexLocation = 0
    for x in ruleSplit:
        if x == 'object-group':
            foundObjectGroup = True
            break
        objectGroupIndexLocation += 1
    if foundObjectGroup:
        objectGroupName = ruleSplit[objectGroupIndexLocation+1]
        tempObjectGroupExpanded = []
        ExpandObjectGroup(objectGroupName)
        firstPart = ''
        for i in range(0,objectGroupIndexLocation):
            firstPart = firstPart + ruleSplit[i] + ' '
        lastPart = ''
        for i in range(objectGroupIndexLocation+2,len(ruleSplit)):
            lastPart = lastPart + ruleSplit[i] + ' '
        for x in tempObjectGroupExpanded:
            tempString = firstPart + x + " " + lastPart
            if 'object-group' in tempString:
                tempExpandedRulesContainsOG.append(tempString)
            else:
                tempExpandedRules.append(tempString)
        
        #Have some rules with OG's still most process them
        while (len(tempExpandedRulesContainsOG) > 0):
            ruleSplit = tempExpandedRulesContainsOG.pop(-1).split()
            objectGroupIndexLocation = 0
            for x in ruleSplit:
                if x == 'object-group':
                    foundObjectGroup = True
                    break
                objectGroupIndexLocation += 1
            if foundObjectGroup:
                objectGroupName = ruleSplit[objectGroupIndexLocation+1]
                tempObjectGroupExpanded = []
                ExpandObjectGroup(objectGroupName)
                firstPart = ''
                for i in range(0,objectGroupIndexLocation):
                    firstPart = firstPart + ruleSplit[i] + ' '
                lastPart = ''
                for i in range(objectGroupIndexLocation+2,len(ruleSplit)):
                    lastPart = lastPart + ruleSplit[i] + ' '
                for x in tempObjectGroupExpanded:
                    tempString = firstPart + x + " " + lastPart
                    if 'object-group' in tempString:
                        tempExpandedRulesContainsOG.append(tempString)
                    else:
                        tempExpandedRules.append(tempString)
        
        #Now Go through the tempExpandedRules array and swap out any "object" stuff. Could be multiples per line
        for x in tempExpandedRules:
            ruleSplit = x.split()
            objectIndexLocation = 0
            for x in ruleSplit:
                if x == 'object':
                    foundObject = True
                    break
                objectGroupIndexLocation += 1    
        if foundObjectGroup:
            objectName = ruleSplit[objectIndexLocation+1]        
                            
        #Test Print    
        #for x in tempExpandedRules:
        #    print x    
    return tempExpandedRules
            
    
    
        
    #print rule
    #print ruleSplit[objectGroupIndexLocation]
            
        
        


def ExpandACL(rootACL):
    global listOfObjectGroups
    #For Each rule in the ACL we to start the expansion process
    

def ExpandObjectGroup(name):
    global listOfObjectGroups
    global tempObjectGroupExpanded
    for x in listOfObjectGroups:
        if x.name == name:
            break
    #x.printDirectItemsOnly()
    tempObjectGroupExpanded = tempObjectGroupExpanded + x.returnClean()
    #objectGroupExpanded.append() 
    for y in x.listOfObjectGroups:
        ExpandObjectGroup(y)




def LineParser(commandName,lineList,line):
    global networkObjectCount, serviceObjectCount, portObjectCount,accessListCount, protocolObjectCount,currentOpenRootCommandLine,currentOpenSubCommandLine \
    ,currentOpenSubSubCommandLine, objectGroupCount, currentOpenRootCommand, currentOpenSubCommand, currentOpenSubSubCommand, \
    listOfHosts,listOfServiceObjects,listOfPortObjects,listOfProtocolObjects,listOfObjectGroups,listOfIcmpObjects,listOfAccessLists,icmpObjectCount, listOfObjects \
    ,listOfAccessGroups, hostname
    
    
    objectExists = False
    
    
    #Handle Command access-group
    if commandName == 'access-group':
        tempAccessGroup = AccessGroup(line)
        listOfAccessGroups.append(tempAccessGroup)
    
    #Handle Command network-object
    if commandName == 'network-object':
                    
        #print commandName +" "+ lineList[1] +" "+ lineList[2]
        if lineList[1] == 'host':
            #tempNetworkObject = NetworkObject(lineList[1])
            #Check if a network-object host already exists
            for x in listOfHosts:
                if x.ipAddy == lineList[2]:
                    objectExists = True
                    if currentOpenRootCommand == 'object-group':
                        #print "add to object-group ",listOfObjectGroups[-1].name
                        listOfObjectGroups[-1].listOfNetworkObjects.append(NetworkObject(lineList[1],lineList,line))
            if objectExists == False:
                listOfHosts.append(NetworkObject(lineList[1],lineList,line))
                networkObjectCount += 1
                if currentOpenRootCommand == 'object-group':
                        listOfObjectGroups[-1].listOfNetworkObjects.append(NetworkObject(lineList[1],lineList,line))
                #listOfHosts.append(tempNetworkObject))
            #else:
            #    print "OBJECT EXISTS", lineList
        elif lineList[1] == 'object':
            #Find the network  object and add it to the groups list
            for x in listOfHosts:
                if x.name == lineList[2]:
                    if currentOpenRootCommand == 'object-group':
                        listOfObjectGroups[-1].listOfNetworkObjects.append(x)
        #assumin a network and subnet for older ASA versions    
        else:
            #Check if a network-object host already exists
            for x in listOfHosts:
                if x.ipAddy == lineList[1] and x.subnet == lineList[2]:
                    objectExists = True
                    if currentOpenRootCommand == 'object-group':
                        listOfObjectGroups[-1].listOfNetworkObjects.append(NetworkObject('network',lineList,line))
            if objectExists == False:
                listOfHosts.append(NetworkObject('network',lineList,line))
                networkObjectCount += 1
                if currentOpenRootCommand == 'object-group':
                        listOfObjectGroups[-1].listOfNetworkObjects.append(NetworkObject('network',lineList,line))
                #listOfHosts.append(tempNetworkObject))
            #else:
            #    print "OBJECT EXISTS", lineList
        #IF this is part of a larger Object-Group we must add it to that
    elif commandName == 'object':
        if currentOpenRootCommand == 'object':
            for o in listOfHosts:
                if o.name == lineList[2]:
                    objectExists = True
            if  objectExists == False:        
                if lineList[1] == 'network':
                    listOfHosts.append(NetworkObject('placeholder',lineList,line))
                    networkObjectCount += 1
                if lineList[1] == 'service':
                    listOfServiceObjects.append(ServiceObject(line))
                    serviceObjectCount += 1
    #Assumes this command is nested under the 'object' command
    #Highly correlated to service-objects
    elif commandName == 'service':
        if currentOpenRootCommand == 'object':
            listOfServiceObjects[-1].parseLine(line)
            
                
    #Assumes this command is nested under the 'object' command
    #Assumes format of "subnet x.x.x.x y.y.y.y'        
    elif commandName == 'subnet':
        if currentOpenRootCommand == 'object':
            listOfHosts[-1].parseLine('network',lineList,line)
            
            
    #Assumes this command is nested under the 'object' command
    #Assumes format of "host x.x.x.x y.y.y.y'        
    elif commandName == 'host':
        if currentOpenRootCommand == 'object':
            listOfHosts[-1].parseLine('network host',lineList,line)    
        
    elif commandName == 'service-object':
        #the 2nd column is protocol which will affect the parsing
        #Check if a service-object host already exists
        #I don't think we really care if service-objects are doubles
        #for x in listOfServiceObjects:
        #    if x.fullLine == line:
        #        objectExists = True
        #        #print "check ", x.fullLine, "TO ", line
        #        #print "ServiceObject Exists " + line
        #    else:
        #        objectExists = False
        objectExists = False
        if lineList[1] == 'object':
            #Find the network  object and add it to the groups list
            for x in listOfServiceObjects:
                if x.name == lineList[2]:
                    objectExists = True
                    if currentOpenRootCommand == 'object-group':
                        listOfObjectGroups[-1].listOfServiceObjects.append(x)
        if currentOpenRootCommand == 'object-group':
            if objectExists == False:
                listOfServiceObjects.append(ServiceObject(line))
                serviceObjectCount += 1
                listOfObjectGroups[-1].listOfServiceObjects.append(ServiceObject(line))
                
    elif commandName == 'port-object':
        for x in listOfPortObjects:
            if x.fullLine ==line:
                objectExists = True
            else:
                objectExists = False
        if objectExists == False:
                listOfPortObjects.append(PortObject(lineList,line))
                portObjectCount += 1
        if currentOpenRootCommand == 'object-group':
                listOfObjectGroups[-1].listOfPortObjects.append(PortObject(lineList,line))
    
                
    elif commandName == 'protocol-object':
        for x in listOfProtocolObjects:
            if x.fullLine ==line:
                objectExists = True
            else:
                objectExists = False
        if objectExists == False:
                listOfProtocolObjects.append(ProtocolObject(lineList,line))
                protocolObjectCount += 1
        if currentOpenRootCommand == 'object-group':
                listOfObjectGroups[-1].listOfProtocolObjects.append(ProtocolObject(lineList,line))
    
    elif commandName == 'icmp-object':
        for x in listOfProtocolObjects:
            if x.fullLine ==line:
                objectExists = True
                
            else:
                objectExists = False
        if objectExists == False:
                listOfIcmpObjects.append(IcmpObject(lineList,line))
                icmpObjectCount += 1
        if currentOpenRootCommand == 'object-group':
                listOfObjectGroups[-1].listOfIcmpObjects.append(IcmpObject(lineList,line))
    
    
    elif commandName == 'object-group':
        objectGroupCount += 1
        listOfObjectGroups.append(ObjectGroup(lineList,line))
            
    elif commandName == 'group-object':
        if currentOpenRootCommand == 'object-group':
                listOfObjectGroups[-1].listOfObjectGroups.append(lineList[1])
    
    elif commandName == 'description':
        splitLineRemoveFirstWord = line.split(' ',2)[2] #might be a problem for commands with deeper whitespace
        if currentOpenRootCommand == 'object-group':
            listOfObjectGroups[-1].description = splitLineRemoveFirstWord
            
    elif commandName == 'access-list':
        accessListCount += 1
        skip = False
        if lineList[2] == 'remark':
            skip = True
        
        for x in listOfAccessLists:
            if lineList[1] == x.name:
                objectExists = True
                break
            else:
                objectExists = False
        if objectExists == False and not skip:
            listOfAccessLists.append(AccessList(lineList))
            listOfAccessLists[-1].listOfRules.append(line)
            
        if objectExists == True and not skip:
            x.listOfRules.append(line)
    
    elif commandName == 'hostname':
            hostname = lineList[1]            
                    