'''
Created on Jun 29, 2013

@author: MrEd


'''

from ConfigParser import SafeConfigParser 
import pysvn
import getpass
import MySQLdb
import re
from  NetworkObject import *
from  ServiceObject import *
from  PortObject import *
from  ProtocolObject import *
from  ObjectGroup import *
from  IcmpObject import *
from  AccessList import *
from  AccessListSubRule import *
from  ObjectNetwork import *
from  AccessGroup import *
from  InterfaceObject import *


def ParseMe(inputFile, options):
	
	listOfCommands = ['hostname', 'name', 'interface', 'object-group', 'network-object', 'description', 'service-object', 'port-object', 'group-object', 'access-list', 'nat', 'static', \
					 'access-group', 'crypto','domain-name','protocol-object','icmp-object', 'object', 'subnet', 'host', 'service']
	listOfCiscoSwitchCommands = ['hostname', 'interface', 'switchport', 'spanning-tree']
	StartOfNewCommandObject = True
	linesIgnored = 0
	linesProcessed = 0
	networkObjectCount = 0
	serviceObjectCount = 0
	portObjectCount = 0
	objectGroupCount = 0
	protocolObjectCount = 0
	icmpObjectCount = 0
	accessListCount = 0
	objectExists = False
	currentWhiteSpaceLevel = 0
	previousLineWhiteSpace = 0
	currentOpenRootCommandLine = 'empty'
	currentOpenRootCommand = 'empty'
	currentOpenSubCommandLine = 'empty'
	currentOpenSubCommand = 'empty'
	currentOpenSubSubCommandLine = 'empty'
	currentOpenSubSubCommand = 'empty'
	
	
	listOfHosts = []
	listOfServiceObjects = []
	listOfPortObjects = []
	listOfProtocolObjects = []
	listOfObjectGroups = []
	listOfIcmpObjects = []
	listOfAccessLists = []
	listOfObjects = []  
	tempObjectGroupExpanded = []
	listOfAccessGroups = []
	listOfInterfaces = []
	hostname = []
	deviceRepoName = 'unknown'
	deviceRepoRevisionNumber = 0
	doSQLStuff = False
	#inputFile = open('exampleConfig.cfg', 'r')
	#inputFile = open('ash.cfg', 'r')
	#outputFile = open('output.txt', 'w')
	#outputFileLargeACLs = open('output-LargeACLs.txt', 'w') #these are super expanded ACL lists
	#outputFileLargeACLsForCopyAndPaste = open('output-LargeACLs-CopyPaste.txt','w')
	#outputFileDebugDump = open('debugDump.txt','w')
	#outputFileLogging = open('LogFile.txt','w')
	
	
	#Use options Dict being passed in
	outputFile = open(options['outputFile'], 'w')
	outputFileLargeACLs = open(options['outputFileLargeACLs'], 'w') #these are super expanded ACL lists
	outputFileLargeACLsForCopyAndPaste = open(options['outputFileLargeACLsForCopyAndPaste'],'w')
	outputFileDebugDump = open(options['outputFileDebugDump'],'w')
	outputFileLogging = open(options['outputFileLogging'],'a')
	DBhost = options['DBhost']
	DBschema = options['DBschema']
	DBuser = options['DBuser']
	DBpassword = options['DBpassword']
	doDebugDump = options['doDebugDump']
	doSQLStuff = options['doSQLStuff']
	deviceConfig = options['deviceConfig']
	deviceRepoRevisionNumber = options['deviceRepoRevisionNumber']
	getFileFrom = options['getFileFrom']
	deviceType = options['deviceType']
	
	#This will return a list[] of a ACL line expanded to every combination. It can be rather large
	#list contains entries like: access-list outside_access_in extended permit tcp 192.168.101.0 255.255.255.0 10.150.130.144 255.255.255.255  eq https
	def ExpandRule(rule,listOfObjectGroups,listOfAccessLists):
		#global listOfObjectGroups, tempObjectGroupExpanded
		#global listOfAccessLists
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
			tempObjectGroupExpanded = ExpandObjectGroup(objectGroupName,listOfObjectGroups)
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
					tempObjectGroupExpanded = ExpandObjectGroup(objectGroupName,listOfObjectGroups)
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
			#Dont think this is working. crashes if the cfg does not have an "object"
			for x in tempExpandedRules:
				ruleSplit = x.split()
				objectIndexLocation = 0
				for x in ruleSplit:
					if x == 'object':
						foundObject = True
						break
					objectGroupIndexLocation += 1	
		#	if foundObjectGroup:
		#		objectName = ruleSplit[objectIndexLocation+1]		
								
			#Test Print	
			#for x in tempExpandedRules:
			#	print x	
		return tempExpandedRules
				
	
	def ExpandObjectGroup(name,listOfObjectGroups):
		listOfObjectGroups
		tempObjectGroupExpanded = []
		for x in listOfObjectGroups:
			if x.name == name:
				break
		#x.printDirectItemsOnly()
		tempObjectGroupExpanded = tempObjectGroupExpanded + x.returnClean()
		#objectGroupExpanded.append() 
		for y in x.listOfObjectGroups:
			ExpandObjectGroup(y,listOfObjectGroups)
		return tempObjectGroupExpanded
	
	
	def ExpandObjectGroupForProtocolAttributes(name,listOfObjectGroups):
		tempObjectGroupExpanded = []
		for x in listOfObjectGroups:
			if x.name == name:
				break
		tempObjectGroupExpanded = tempObjectGroupExpanded + x.returnProtocolAttributes()
		for y in x.listOfObjectGroups:
			ExpandObjectGroupForProtocolAttributes(y,listOfObjectGroups)
		return tempObjectGroupExpanded
	
	def ExpandObjectGroupForDestPorts(name,listOfObjectGroups):
		tempObjectGroupExpanded = []
		for x in listOfObjectGroups:
			if x.name == name:
				break
		tempObjectGroupExpanded = tempObjectGroupExpanded + x.returnDestPorts()
		for y in x.listOfObjectGroups:
			ExpandObjectGroupForDestPorts(y,listOfObjectGroups)
		return tempObjectGroupExpanded
	
	def LineParser(commandName,lineList,line):
		networkObjectCount = 0
		serviceObjectCount = 0
		portObjectCount = 0
		accessListCount = 0
		protocolObjectCount = 0
		objectGroupCount = 0
		icmpObjectCount = 0
		interfaceObjectCount = 0
		
		currentOpenRootCommandLine
		currentOpenSubCommandLine
		currentOpenSubSubCommandLine
		currentOpenRootCommand
		currentOpenSubCommand
		currentOpenSubSubCommand
		listOfHosts
		listOfServiceObjects
		listOfPortObjects
		listOfProtocolObjects
		listOfObjectGroups
		listOfIcmpObjects
		listOfAccessLists
		listOfObjects
		listOfInterfaces
		hostname
				
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
				#	print "OBJECT EXISTS", lineList
			elif lineList[1] == 'object':
				#Find the network  object and add it to the groups list
				for x in listOfHosts:
					if x.name == lineList[2]:
						if currentOpenRootCommand == 'object-group':
							listOfObjectGroups[-1].listOfNetworkObjects.append(x)
			#assuming a network and subnet for older ASA versions	
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
				#	print "OBJECT EXISTS", lineList
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
			#	if x.fullLine == line:
			#		objectExists = True
			#		#print "check ", x.fullLine, "TO ", line
			#		#print "ServiceObject Exists " + line
			#	else:
			#		objectExists = False
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
					listOfObjectGroups[-1].listOfServiceObjects.append(ServiceObject(line))
		
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
				hostname.append(lineList[1])	
		#Handle interface command
		elif commandName == 'interface':
			for x in listOfInterfaces:
				if x.interface == lineList[1]:
					objectExists = True
				else:
					objectExists = False
			if objectExists == False:
					listOfInterfaces.append(InterfaceObject(line))
					interfaceObjectCount += 1
		#Handle switchport command. probably nested
		elif commandName == 'spanning-tree':
			if currentOpenRootCommand == 'interface':
					if lineList[1] == 'portfast':
						listOfInterfaces[-1].setSpanningtreePortfastEnabled(True)
		elif commandName == 'switchport':
			if currentOpenRootCommand == 'interface':
					if lineList[1] == 'mode':
						listOfInterfaces[-1].setSwitchportMode(lineList[2])
					if lineList[1] == 'access':
						if lineList[2] == 'vlan':
							listOfInterfaces[-1].setAccessVlan(lineList[3])
					if lineList[1] == 'voice':
						if lineList[2] == 'vlan':
							listOfInterfaces[-1].setVoiceVlan(lineList[3])	
		
						
	# When parsing through the lines we need to check if the line starts with whitespace or not
	
	
	#FUN STUFF BELOW HERE
	
	#Load Into SQL DB
	
	def SqlUploadInterfaces(interfaceObject,cur,hostname,listOfInterfaces):
		
		interface = interfaceObject.interface
		access_vlan = interfaceObject.accessVlan
		voice_vlan = interfaceObject.voiceVlan
		spanningtree_portfast_enabled = interfaceObject.spanningtreePortfastEnabled
		switchport_mode = interfaceObject.switchportMode
		
		with con:
			cur.execute("INSERT INTO interfaces (device_repo_name,revision_number,hostname,interface,access_vlan,voice_vlan,spanningtree_portfast_enabled,switchport_mode)\
			values ('%s','%d','%s','%s','%s','%s','%d','%s')" % (deviceConfig,deviceRepoRevisionNumber,hostname,interface,access_vlan,voice_vlan,spanningtree_portfast_enabled,switchport_mode))
					
	
	def SqlUploadAclSubrules(aclSubRule,cur,listOfHosts,listOfObjectGroups,hostname):
		#global tempObjectGroupExpanded, listOfHosts, hostname,listOfObjectGroups
		list1 = []
		list2 = []
		list3 = []
		list4 = []
		list5 = []
		
		
		#PROTO
		#if aclSubRule.protocolIsOG == True:
		#	#c1longest = len(aclSubRule.protocol) + len(' object-group')
		#	tempObjectGroupExpanded = []
		#	tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.protocol,listOfObjectGroups)
		#	list1 = tempObjectGroupExpanded
		if aclSubRule.protocolIsO == True:
			for x in listOfServiceObjects:
				if x.name == aclSubRule.protocol:
					break
			list1 = [x.protocol]
			tempStr = x.dest_operator
			if tempStr == 'range':
				tempStr = tempStr + " " + x.dest_startRange + " " + x.dest_stopRange
			else:
				tempStr = tempStr + " " + x.dest_port	
			list5 = [tempStr]	
		elif aclSubRule.protocolIsOG == True:
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroupForProtocolAttributes(aclSubRule.protocol,listOfObjectGroups)
			list1 = tempObjectGroupExpanded 
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroupForDestPorts(aclSubRule.protocol,listOfObjectGroups)
			list5 = tempObjectGroupExpanded	
		elif aclSubRule.protocol != 'unknown':
				list1 = [aclSubRule.protocol]
		#SOURCE 
		if aclSubRule.sourceIsOG == True:
			#c2longest = len(aclSubRule.source) + len(' object-group')
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.source,listOfObjectGroups)
			list2 = tempObjectGroupExpanded
		elif aclSubRule.sourceIsO == True:
			#look up the network object
			for o in listOfHosts:
				if o.name == aclSubRule.source:
					tempStr = o.ipAddy + " " + o.subnet
					list2 = [tempStr]
		else:
			if aclSubRule.source != 'unknown':
				list2 = [aclSubRule.source]
		#SOURCE PORTS
		if aclSubRule.source_portIsOG == True:
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.source_port,listOfObjectGroups)
			list3 = tempObjectGroupExpanded
		else:
			if aclSubRule.source_port !='unknown':
				list3 =  [aclSubRule.source_port]
		#DEST
		if aclSubRule.destIsOG == True:
			#c4longest = len(aclSubRule.dest) + len(' object-group')
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.dest,listOfObjectGroups)
			list4 = tempObjectGroupExpanded
		elif aclSubRule.destIsO == True:
			#look up the network object
			for o in listOfHosts:
				if o.name == aclSubRule.dest:
					tempStr = o.ipAddy + " " + o.subnet
					list4 = [tempStr]
		else:
			if aclSubRule.dest != 'unknown':
				list4 =  [aclSubRule.dest]
		#DEST PORTS
		if aclSubRule.dest_portIsOG == True:
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.dest_port,listOfObjectGroups)
			list5 = tempObjectGroupExpanded
		else:
			if aclSubRule.dest_port != 'unknown':
				list5 = [aclSubRule.dest_port]
		
		#Create SQL queries to load list1 - list5 into the databse
		ex_list1 = ''
		n = len(list1)
		m = 0
		for a in list1:
			m += 1
			if m == n:
				ex_list1 = ex_list1 + a
			else:
				ex_list1 = ex_list1 + a + ","
		ex_list2 = ''
		n = len(list2)
		m = 0
		for a in list2:
			m += 1
			if m == n:
				ex_list2 = ex_list2 + a
			else:
				ex_list2 = ex_list2 + a + ","
		ex_list3 = ''
		n = len(list3)
		m = 0
		for a in list3:
			m += 1
			if m == n:
				ex_list3 = ex_list3 + a
			else:
				ex_list3 = ex_list3 + a + ","
		ex_list4 = ''
		n = len(list4)
		m = 0
		for a in list4:
			m += 1
			if m == n:
				ex_list4 = ex_list4 + a
			else:
				ex_list4 = ex_list4 + a + ","
		ex_list5 = ''
		n = len(list5)
		m = 0
		for a in list5:
			m += 1
			if m == n:
				ex_list5 = ex_list5 + a
			else:
				ex_list5 = ex_list5 + a + ","
	
		with con:
			#cur = con.curser()
			cur.execute("INSERT INTO access_list_subrules (device_repo_name,revision_number,hostname,access_list_name,full_line,access_list_type,type_of_access,protocol,source,source_operator,source_port,dest,dest_operator,dest_port,icmp_type,protocol_expanded_group\
			,source_expanded_group,dest_expanded_group,source_port_expanded_group,dest_port_expanded_group) values ('%s','%d','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"\
			 % (deviceConfig,deviceRepoRevisionNumber,hostname,aclSubRule.accessListName,aclSubRule.fullLine,\
			aclSubRule.accessListType,aclSubRule.typeOfAccess,aclSubRule.protocol,\
			aclSubRule.source,aclSubRule.source_operator,aclSubRule.source_port,aclSubRule.dest,aclSubRule.dest_operator,aclSubRule.dest_port,aclSubRule.icmp_type,ex_list1,ex_list2,ex_list4,ex_list3,ex_list5))

	def ExpandExtendedAclForHuman(aclSubRule,listOfHosts,listOfObjectGroups,listOfServiceObjects):
		#global tempObjectGroupExpanded, listOfHosts, listOfObjectGroups
		list1 = []
		list2 = []
		list3 = []
		list4 = []
		list5 = []
		c1 = ''
		c2 = ''
		c3 = ''
		c4 = ''
		c5 = ''
		c1longest,c2longest,c3longest,c4longest,c5longest = 0,0,0,0,0
		if aclSubRule.protocol == 'unknown':
			c1longest = 0
		else: c1longest = 8
		if aclSubRule.source == 'unknown':
			c2longest = 0
		else: c2longest = 10
		if aclSubRule.source_port == 'unknown':
			c3longest = 0
		else: c3longest = 12
		if aclSubRule.dest == 'unknown':
			c4longest = 0
		else: c4longest = 15
		if aclSubRule.dest_port == 'unknown':
			c5longest = 0
		else: c5longest = 17
		outputFile.write(aclSubRule.fullLine)

		if aclSubRule.protocolIsO == True:
			for x in listOfServiceObjects:
				if x.name == aclSubRule.protocol:
					break
			list1 = [x.protocol]
			tempStr = x.dest_operator
			if tempStr == 'range':
				tempStr = tempStr + " " + x.dest_startRange + " " + x.dest_stopRange
			else:
				tempStr = tempStr + " " + x.dest_port	
			list5 = [tempStr]
		elif aclSubRule.protocolIsOG == True:
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroupForProtocolAttributes(aclSubRule.protocol,listOfObjectGroups)
			list1 = tempObjectGroupExpanded 
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroupForDestPorts(aclSubRule.protocol,listOfObjectGroups)
			list5 = tempObjectGroupExpanded
		elif aclSubRule.protocol != 'unknown':
				list1 = [aclSubRule.protocol]
		#SOURCE 
		if aclSubRule.sourceIsOG == True:
			#c2longest = len(aclSubRule.source) + len(' object-group')
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.source,listOfObjectGroups)
			list2 = tempObjectGroupExpanded
		elif aclSubRule.sourceIsO == True:
			#look up the network object
			for o in listOfHosts:
				if o.name == aclSubRule.source:
					tempStr = o.ipAddy + " " + o.subnet
					#print tempStr
					list2 = [tempStr]
		else:
			if aclSubRule.source != 'unknown':
				list2 = [aclSubRule.source]
				#c2longest = len(aclSubRule.source) + len(' 255.255.255.255')
		#SOURCE PORTS
		if aclSubRule.source_portIsOG == True:
			#c3longest = len(aclSubRule.source_port) + len(' object-group')
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.source_port,listOfObjectGroups)
			list3 = tempObjectGroupExpanded
		else:
			if aclSubRule.source_port !='unknown':
				list3 =  [aclSubRule.source_port]
		#DEST
		if aclSubRule.destIsOG == True:
			#c4longest = len(aclSubRule.dest) + len(' object-group')
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.dest,listOfObjectGroups)
			list4 = tempObjectGroupExpanded
		elif aclSubRule.destIsO == True:
			#look up the network object
			for o in listOfHosts:
				if o.name == aclSubRule.dest:
					tempStr = o.ipAddy + " " + o.subnet
					list4 = [tempStr]
		else:
			if aclSubRule.dest != 'unknown':
				list4 =  [aclSubRule.dest]
				#c4longest = len(aclSubRule.dest) + len(' 255.255.255.255')
		#DEST PORTS
		if aclSubRule.dest_portIsOG == True:
			#c5longest = len(aclSubRule.dest_port) + len(' object-group')
			tempObjectGroupExpanded = []
			tempObjectGroupExpanded = ExpandObjectGroup(aclSubRule.dest_port,listOfObjectGroups)
			list5 = tempObjectGroupExpanded
		
		else:
			if aclSubRule.dest_port != 'unknown':
				list5 = [aclSubRule.dest_port]
		#Find the longest length in each column in the lists
		for n in list1:
			if len(n) > c1longest:
				c1longest = len(n)
		for n in list2:
			if len(n) > c2longest:
				c2longest = len(n)
		for n in list3:
			if len(n) > c3longest:
				c3longest = len(n)
		for n in list4:
			if len(n) > c4longest:
				c4longest = len(n)
		for n in list5:
			if len(n) > c5longest:
				c5longest = len(n)
		c1PadMe,c2PadMe,c3PadMe,c4PadMe,c5PadMe = 0,0,0,0,0
		#Find Longest List so we know max rows
		x = len(list1)
		if len(list2) > x: x = len(list2)
		if len(list3) > x: x = len(list3)
		if len(list4) > x: x = len(list4)
		if len(list5) > x: x = len(list5)
		
		#FIRST LINE ONLY
		s0 = 'access-list'
		s1 = aclSubRule.accessListName
		s2 = aclSubRule.accessListType
		s3 = aclSubRule.typeOfAccess
		sFirst = s0 + ' ' + s1 + ' ' + s2 + ' ' + s3
		sFirstPad = (' ' * len(sFirst))
		#Add Column Names at the top, but only if they have  values
		if aclSubRule.protocol == 'unknown':
			topCol1 = ''
		else: 
			topCol1 = 'Protocol '
			#if c1longest < 9: c1longest = 9
			c1PadMe = c1longest - 9
		if aclSubRule.source == 'unknown':
			topCol2 = ''
		else:
			topCol2 = 'Source-IPs '
			#if c1longest < 11: c1longest = 11
			c2PadMe = c2longest - 11
		if aclSubRule.source_port == 'unknown':
			topCol3 = ''
		else:
			topCol3 = 'Source-Ports '
			#if c1longest < 13: c1longest = 13
			c3PadMe = c3longest - 13
		if aclSubRule.dest == 'unknown':
			topCol4 = ''
		else:
			topCol4 = 'Destination-IPs '
			#if c4longest < 16: c4longest = 16
			c4PadMe = c4longest - 16
		if aclSubRule.dest_port == 'unknown':
			topCol5 = ''
		else:
			topCol5 = 'Destination-Ports '
			#if c1longest < 18: c1longest = 18
			c5PadMe = c5longest - 18
		topRowPad1 = (' ' * c1PadMe)
		topRowPad2 = (' ' * c2PadMe)
		topRowPad3 = (' ' * c3PadMe)
		topRowPad4 = (' ' * c4PadMe)
		topRowPad5 = (' ' * c5PadMe)
		c1,c2,c3,c4,c5 = '','','','',''
		fpad1,fpad2,fpad3,fpad4,fpad5 = '','','','',''
		if len(list1) > 0:
			c1 = list1.pop(0)
			fpad1 = ' '
			c1PadMe = c1longest - len(c1)
		if len(list2) > 0:
			c2 = list2.pop(0)
			fpad2 = ' '
			c2PadMe = c2longest - len(c2)
		if len(list3) > 0:
			c3 = list3.pop(0)
			fpad3 = ' '
			c3PadMe = c3longest - len(c3)
		if len(list4) > 0:
			c4 = list4.pop(0)
			fpad4 = ' '
			c4PadMe = c4longest - len(c4)
		if len(list5) > 0:
			c5 = list5.pop(0)
			fpad5 = ' '
			c5PadMe = c5longest - len(c5)
		x = x - 1
		pad1 = (' ' * c1PadMe)
		pad2 = (' ' * c2PadMe)
		pad3 = (' ' * c3PadMe)
		pad4 = (' ' * c4PadMe)
		pad5 = (' ' * c5PadMe)
		pad0 = (' ' * len(sFirst))
		string1 = pad0 +' '+c1+pad1+fpad2+c2+pad2+fpad3+c3+pad3+fpad4+c4+pad4+fpad5+c5+pad5+'\n'
		topRow = sFirst +' '+topCol1+topRowPad1+fpad2+topCol2+topRowPad2+fpad3+topCol3+topRowPad3+fpad4+topCol4+topRowPad4+fpad5+topCol5+'\n'
		outputFile.write(topRow)
		outputFile.write(string1)
		# THE REST OF LINES
		while x > 0:
			fpad1,fpad2,fpad3,fpad4,fpad5 = '','','','',''
			c1,c2,c3,c4,c5 = '','','','',''
			if len(list1) > 0:
				c1 = list1.pop(0)
				fpad2 = ' '
				c1PadMe = c1longest - len(c1)
			else: 
				if c1longest != 0: c1PadMe = c1longest +1
			if len(list2) > 0:
				c2 = list2.pop(0)
				fpad3 = ' '
				c2PadMe = c2longest - len(c2)
			else:
				if c2longest != 0: c2PadMe = c2longest +1
			if len(list3) > 0:
				c3 = list3.pop(0)
				fpad4 = ' '
				c3PadMe = c3longest - len(c3)
			else: 
				if c3longest != 0: c3PadMe = c3longest +1
			if len(list4) > 0:
				c4 = list4.pop(0)
				fpad5 = ' '
				c4PadMe = c4longest - len(c4)
			else: 
				if c4longest != 0: c4PadMe = c4longest +1
			if len(list5) > 0:
				c5 = list5.pop(0)
				#fpad5 = ' '
				c5PadMe = c5longest - len(c5)
			else: 
				if c5longest != 0: c5PadMe = c5longest  +1
			x = x - 1
			pad1 = (' ' * c1PadMe)
			pad2 = (' ' * c2PadMe)
			pad3 = (' ' * c3PadMe)
			pad4 = (' ' * c4PadMe)
			pad5 = (' ' * c5PadMe)
			string1 = sFirstPad+' '+c1+pad1+fpad2+c2+pad2+fpad3+c3+pad3+fpad4+c4+pad4+fpad5+c5+pad5+'\n'
			outputFile.write(string1)
		
	def PrintStandardAclForHuman(aclSubRule):
		outputFile.write(aclSubRule.fullLine)
	
	print "****************START PARSING CONFIG****************"
	#START PARSING THE inputFile
	for line in inputFile:
		linesProcessed += 1
		lineList = line.split()
		#print line
		#print currentOpenRootCommand
		whiteSpace = len(line) - len(line.lstrip())
		#print whiteSpace
		if line == '\n':
			if doDebugDump:
				outputFileDebugDump.write("BLANK LINE!\n")
		elif line[0] != ' ':
			currentWhiteSpaceLevel = 0
			currentOpenRootCommandLine = line
			currentOpenRootCommand = lineList[0]
			#print "NO Whitespace - Start of new command CWL=",currentWhiteSpaceLevel," ",line
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				#outputFileDebugDump.write("PARSING - THIS COMMAND " + lineList[0] + "\n")
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				#outputFileDebugDump.write("IGNORE - THIS COMMAND NOT IN LIST " + lineList[0] + "\n") 
		elif whiteSpace > 0 and currentWhiteSpaceLevel == 0:
			currentWhiteSpaceLevel += 1
			currentOpenSubCommandLine = line
			currentOpenSubCommandLine = lineList[0]
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				#outputFileDebugDump.write("PARSING - THIS COMMAND " + lineList[0] + "\n")
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				#outputFileDebugDump.write("IGNORE - THIS COMMAND NOT IN LIST " + lineList[0] + "\n")
			#outputFileDebugDump.write("2nd if CURRENT WHITE SPACE LEVEL= "+ str(currentWhiteSpaceLevel) + "\n")
		
		elif whiteSpace > 0 and whiteSpace == previousLineWhiteSpace:
			currentWhiteSpaceLevel = currentWhiteSpaceLevel
			currentOpenSubCommandLine = line
			currentOpenSubCommandLine = lineList[0]
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				#outputFileDebugDump.write("PARSING - THIS COMMAND " + lineList[0] + "\n")
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				#outputFileDebugDump.write("IGNORE - THIS COMMAND NOT IN LIST " + lineList[0] + "\n")
			#outputFileDebugDump.write("3rd if CURRENT WHITE SPACE LEVEL= ", str(currentWhiteSpaceLevel) + "\n")
	
		elif whiteSpace > 0 and whiteSpace > previousLineWhiteSpace:
			currentWhiteSpaceLevel += 1
			currentOpenSubSubCommandLine = line
			currentOpenSubSubCommandLine = lineList[0]
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				#outputFile.write("PARSING - THIS COMMAND " + lineList[0] + "\n")
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				#outputFileDebugDump.write("IGNORE - THIS COMMAND NOT IN LIST " + lineList[0] + "\n")
			#outputFileDebugDump.write("4th if CURRENT WHITE SPACE LEVEL= ", str(currentWhiteSpaceLevel) + "\n")
		previousLineWhiteSpace = whiteSpace		

	#Break down each AccessList Rule into object based Sub Rules
	for tempACL in listOfAccessLists:    #Each ACL 
		for ruleInACL in tempACL.listOfRules:		# each rule part of the ACL
			#print ruleInACL		
			tempSubRuleObject = AccessListSubRule(ruleInACL)
			tempACL.accessListSubRuleList.append(tempSubRuleObject)
	#ABOVE here is required code for processing a config
	
	#Start SQLDB LOADING STUFF
	if doSQLStuff == True:
		isAlreadyInDB = False
		isLastestRevisionNumberFoundInDB = False
		#isNewDevice = True
		con = MySQLdb.connect(host=DBhost,user=DBuser,passwd=DBpassword,db=DBschema)
		cur = con.cursor()
		#Check what the last revision number parsed is
		cur.execute("SELECT last_parsed_revision FROM parsed_revisions where device_repo_name=%s",(deviceConfig))
		numberRows = int(cur.rowcount)
		if numberRows > 0:
			isAlreadyInDB = True
		lastestRevisionNumberFoundInDB = 0
		for i in range(numberRows):
			row=cur.fetchone()
			if row[0] > lastestRevisionNumberFoundInDB:
				lastestRevisionNumberFoundInDB = row[0]
		print "latest revision in DB is " + str(lastestRevisionNumberFoundInDB)	#A long value
		print "Device Repo revision number is " + str(deviceRepoRevisionNumber)	#an int value
		outputFileLogging.write(deviceConfig +": Latest revision number found in Database is " + str(lastestRevisionNumberFoundInDB) + "\n")
		outputFileLogging.write(deviceConfig +": Revision number for parsed config is " + str(deviceRepoRevisionNumber) + "\n")
		#If this is a local file we want to force a higher new revision number so it updates the DB
		if getFileFrom == 'local':
			deviceRepoRevisionNumber = lastestRevisionNumberFoundInDB + 1
			outputFileLogging.write(deviceConfig +": Local file load : force revision increment to " + str(deviceRepoRevisionNumber) + "\n")
		if (lastestRevisionNumberFoundInDB == deviceRepoRevisionNumber):
			print "Latest revision number found in DB is equal to the device repo version: No Upload to DB"
			outputFileLogging.write(deviceConfig +": Latest revision is in the DB : No Upload to DB \n")
			isLastestRevisionNumberFoundInDB = True
		else: 
			print "Latest revision is not found in the DB : proceed with DB update"
			outputFileLogging.write(deviceConfig +": Latest revision is not found in the DB : proceed with DB update \n")
		
		#Load stuff in the Database		
		count = 0
		countInterfaces = 0
		if (isLastestRevisionNumberFoundInDB == False or isAlreadyInDB == False):
			#Load the objects from listOfAccessLists into the DB
			for x in listOfAccessLists:
				for y in x.accessListSubRuleList:
					SqlUploadAclSubrules(y,cur,listOfHosts,listOfObjectGroups,hostname[0])
					count = count + 1
			print str(count) + "  ACLs SQL UPLOADED"
			outputFileLogging.write(deviceConfig + ": " + str(count) + " ACLs SQL UPLOADED\n")
			#Load the objects from the listOfInterfaces	
			for x in listOfInterfaces:
				SqlUploadInterfaces(x,cur,hostname[0],listOfInterfaces)
				countInterfaces = countInterfaces + 1
			print str(countInterfaces) + " Interfaces SQL UPLOADED"
			outputFileLogging.write(deviceConfig + ": " + str(countInterfaces) + " Interfaces SQL UPLOADED\n")
			
				
			if isAlreadyInDB:
				print "The Device is already in DB, updating the revision numbers to " + str(deviceRepoRevisionNumber)
				#cur.execute("UPDATE parsed_revisions SET last_parsed_revision=44 WHERE device_repo_name='10.45.6.10' " ) 
				cur.execute("UPDATE parsed_revisions SET last_parsed_revision=%s WHERE device_repo_name='%s' " % (deviceRepoRevisionNumber,deviceConfig)) 
				print cur.rowcount
				con.commit()
			else:
				print "Device Not found in DB - Adding it"
				cur.execute("INSERT INTO parsed_revisions (device_repo_name,last_parsed_revision) values ('%s','%d')" % (deviceConfig,deviceRepoRevisionNumber)) 
				con.commit()
				if count > 0:
					print "Clean Up DB for old revisions"
					#print deviceConfig
		with con:
			cur.execute("DELETE FROM "+DBschema+".access_list_subrules where device_repo_name = %s AND revision_number < %s",(deviceConfig,deviceRepoRevisionNumber))
			outputFileLogging.write(deviceConfig + ": " + str(cur.rowcount)+" Rows Deleted From ACL Table\n")
			print "Deleted " + str(cur.rowcount) + " Rows From ACL Table"  	
		with con:
			cur.execute("DELETE FROM "+DBschema+".interfaces where device_repo_name = %s AND revision_number < %s",(deviceConfig,deviceRepoRevisionNumber))
			outputFileLogging.write(deviceConfig + ": " + str(cur.rowcount)+" Rows Deleted From Interfaces Table\n")
			print "Deleted " + str(cur.rowcount) + " Rows From Interfaces Table" 	
	
	if doDebugDump == True:
		outputFileDebugDump.write('STARTING DEBUG DUMP')
	
	#Test Dumping Access Groups
	outputFile.write('******ACL Applied to each Interface******\n')
	for x in listOfAccessGroups:
		outputFile.write('Interface: '+x.interfaceAppliedTo+' '+x.direction+' ACL: '+x.aclApplied+'\n')

	#Test for dumping all ACL sub rules for human readable
	for x in listOfAccessLists:
		outputFile.write('*********************START OF ACL************************\n')
		#Check if this AccessList is applied to an interface
		for z in listOfAccessGroups:
			if z.aclApplied == x.name:
				outputFile.write('*********************Applied to interface: '+z.interfaceAppliedTo+' '+z.direction+'*********************\n')
		for y in x.accessListSubRuleList:
			if y.accessListType == 'extended':
				ExpandExtendedAclForHuman(y,listOfHosts,listOfObjectGroups,listOfServiceObjects)
				outputFile.write ("\n")
				#outputFile.write('**********************END OF ACL*************************\n')
			elif y.accessListType == 'standard': 
				#outputFile.write('*********************START OF ACL************************\n')
				PrintStandardAclForHuman(y)
		outputFile.write('**********************END OF ACL*************************\n')
	
	#Print all network objects
	outputFileDebugDump.write("=================------------------DUMP listOfHosts[]--------------===================\n")
	for x in listOfHosts:
		outputFileDebugDump.write("******************\n")
		outputFileDebugDump.write(x.fullLine)
		x.writeToDebugLog(outputFileDebugDump)
	outputFileDebugDump.write("=================------------------DUMP listOfServiceObjects[]--------------===================\n")
	#Print all service objects
	for x in listOfServiceObjects:
		outputFileDebugDump.write("******************\n")
		outputFileDebugDump.write(x.fullLine)
		x.writeToDebugLog(outputFileDebugDump)
	#Print all accessListSubRules - These are each ACE in a ACL broken down into an object
	outputFileDebugDump.write("=================------------------DUMP listOfAccessLists[] and each accessListSubRuleList[]--------------===================\n")
	for x in listOfAccessLists:
		for y in x.accessListSubRuleList:
			outputFileDebugDump.write("******************\n")
			outputFileDebugDump.write(y.fullLine)
			y.writeToDebugLog(outputFileDebugDump)
	#Print all Prototcol objects in the listOfProtocolObjects[]
	outputFileDebugDump.write("=================------------------DUMP listOfPortObjects[]--------------===================\n")
	for x in listOfPortObjects:
		outputFileDebugDump.write("******************\n")
		outputFileDebugDump.write(x.fullLine)
		x.writeToDebugLog(outputFileDebugDump)
	#Print all Prototcol objects in the listOfProtocolObjects[]
	outputFileDebugDump.write("=================------------------DUMP listOfIcmpObjects[]--------------===================\n")
	for x in listOfIcmpObjects:
		outputFileDebugDump.write("******************\n")
		outputFileDebugDump.write(x.fullLine)
		x.writeToDebugLog(outputFileDebugDump)
	#Print all Prototcol objects in the listOfProtocolObjects[]
	outputFileDebugDump.write("=================------------------DUMP listOfProtocolObjects[]--------------===================\n")
	for x in listOfProtocolObjects:
		outputFileDebugDump.write("******************\n")
		outputFileDebugDump.write(x.fullLine)
		x.writeToDebugLog(outputFileDebugDump)
	#Print all the object groups in the listOfObjectGroups[] 
	outputFileDebugDump.write("=================------------------DUMP listOfObjectGroups[] One Level--------------===================\n")
	for x in listOfObjectGroups:
		outputFileDebugDump.write("******************\n")
		x.writeToDebugLogDirectItemsOnly(outputFileDebugDump)
	outputFileDebugDump.write("=================------------------DUMP listOfInterfaces[]---------------======================\n")
	for x in listOfInterfaces:
		x.writeToDebugLog(outputFileDebugDump)

	#print "NumberOfObjectGroups ",len(listOfObjectGroups)
	#for x in listOfObjectGroups:
	#	print "*****START OF OBJECT GROUP"
	#	if x.typeOfObjectGroup == 'service':
	#		print x.name,x.typeOfServiceGroup
	#	else:
	#		print x.name
	#	x.printDirectItemsOnly()
	#	for y in x.listOfObjectGroups:
			#print "YABBA YABBA DO", y
	#		ExpandObjectGroup(y)
	#	print "*****STOP OF OBJECT GROUP"
	#for x in listOfAccessLists:
	#	#print x.name
		#for y in x.listOfRules:
		#	print "SUB RULE ", y

	#TESTING ACL sub rule stuff
	#for x in listOfAccessLists:
		#number = 8
		#f x.name == 'dev16_access_in':
		#break
		
	#	for y in x.accessListSubRuleList:
	#		print "******************************************************************"
	#		print y.fullLine
	#		print 'name',y.accessListName
	#		print 'type',y.accessListType
	#		print 'typeOfAccess',y.typeOfAccess
	#		print 'Protocol',y.protocol
	#		print 'source',y.source
	#		print 'source Op',y.source_operator
	#		print 'source Port',y.source_port
	#		print 'dest',y.dest
	#		print 'dest Op',y.dest_operator
	#		print 'dest Port',y.dest_port
	#		print 'icmp-type',y.icmp_type
	#		print "******************************************************************"	
	
	#TESING to print object based ACL sub rule
	#for x in listOfAccessLists:
	#number = 8
	#if x.name == 'dev16_access_in':
	#	break
	#print x.accessListSubRuleList[number].fullLine
	#print 'name',x.accessListSubRuleList[number].accessListName
	#print 'type',x.accessListSubRuleList[number].accessListType
	#print 'typeOfAccess',x.accessListSubRuleList[number].typeOfAccess
	#print 'Protocol',x.accessListSubRuleList[number].protocol
	#print 'source',x.accessListSubRuleList[number].source
	#print 'source Op',x.accessListSubRuleList[number].source_operator
	#print 'source Port',x.accessListSubRuleList[number].source_port
	#print 'dest',x.accessListSubRuleList[number].dest
	#print 'dest Op',x.accessListSubRuleList[number].dest_operator
	#print 'dest Port',x.accessListSubRuleList[number].dest_port
	#print 'icmp-type',x.accessListSubRuleList[number].icmp_type
	
	#TESTING FOR super expanding all ACLs
	
	outputFileLargeACLs.write('******ACL Applied to each Interface******\n')
	for x in listOfAccessGroups:
		outputFileLargeACLs.write('Interface: '+x.interfaceAppliedTo+' '+x.direction+' ACL: '+x.aclApplied+'\n')
	outputFileLargeACLs.write('*****END ACL Applied to each Interface*******\n')
	for x in listOfAccessLists:
		for z in listOfAccessGroups:
			if z.aclApplied == x.name:
				outputFileLargeACLs.write('*********************Applied to interface: '+z.interfaceAppliedTo+' '+z.direction+'*********************\n')
		outputFileLargeACLs.write('******ACL Name: ' + x.name + '\n')
		for y in x.listOfRules:
			tempExpandedRules = ExpandRule(y,listOfObjectGroups,listOfAccessLists)
			for z in tempExpandedRules:
				outputFileLargeACLs.write(z + '\n')
		outputFileLargeACLs.write('\n')
	
	#Super Expand all ACL's for copy and paste into Routers/Switches without network objects
	outputFileLargeACLsForCopyAndPaste.write('******ACL Applied to each Interface******\n')
	for x in listOfAccessGroups:
		outputFileLargeACLsForCopyAndPaste.write('Interface: '+x.interfaceAppliedTo+' '+x.direction+' ACL: '+x.aclApplied+'\n')
	outputFileLargeACLsForCopyAndPaste.write('*****END ACL Applied to each Interface*******\n')
	for x in listOfAccessLists:
		for z in listOfAccessGroups:
			if z.aclApplied == x.name:
				outputFileLargeACLsForCopyAndPaste.write('*********************Applied to interface: '+z.interfaceAppliedTo+' '+z.direction+'*********************\n')
		outputFileLargeACLsForCopyAndPaste.write('******ACL Name: ' + x.name + '\n')
		#WE need to print the command to create the IP list ex: ip access-list extended aclname
		#Get the first AccessListSubRule in the listOfRules.accessListSubRuleList to pull the values
		tempS1 = x.accessListSubRuleList[0].accessListType
		commandStartACL = "ip access-list " + tempS1 + " " + x.name
		outputFileLargeACLsForCopyAndPaste.write(commandStartACL+"\n")
		#print x.name
		for y in x.listOfRules:
			tempExpandedRules = ExpandRule(y,listOfObjectGroups,listOfAccessLists)
			for z in tempExpandedRules:
				pattern = re.compile('(deny|permit)[^/]*$', re.IGNORECASE)
				#pattern = re.compile('permit', re.IGNORECASE)
				match = pattern.search(z)
				#print match.group()
				if match:
					outputFileLargeACLsForCopyAndPaste.write(" " + match.group() + '\n')
					#print 'Match Found: ', match.group()
				#else:
				#	print 'no Match'
				#outputFileLargeACLsForCopyAndPaste.write(z+ '\n')
				#print z
			#print y
		outputFileLargeACLsForCopyAndPaste.write('\n')
		#for y in x.listofRules:
		#	tempExpandedRules = ExpandRule(y)
		#for x in tempExpandedRules:
			#print x	
	
	#TEST TO PRINT ALL object objects
	#for x in listOfObjects:
	#	x.printVar()
	#	one = 1
	
	#ExpandRule(listOfAccessLists[1].listOfRules[1])
	
	#tempObjectGroupExpanded = []
	#ExpandObjectGroup('ABC_CORPORATE')
	#for x in tempObjectGroupExpanded:
	#	print x
	
	#	x.printListCounts()
	#print listOfObjectGroups[5].name,len(listOfObjectGroups[5].listOfNetworkObjects)
	#listOfObjectGroups[5].printListCounts()
	
	print "Hostname = " + hostname[0]
	print "Lines Processed = " + str(linesProcessed)
	print "Lines Ignored = " + str(linesIgnored) 
	print "****************STOP PARSING CONFIG****************"
	#print "Network Object Count (Unique)= " + str(networkObjectCount)
	#print "Service Object Count (Unique)= " + str(serviceObjectCount)
	#print "Port Object Count (Unique)= " + str(portObjectCount)
	# print "Protocol Object Count (Unique)= " + str(protocolObjectCount)
	# print "Object Group Count (Unique)= " + str(objectGroupCount)
	# print "ICMP Object Count (Unique)= " + str(icmpObjectCount)
	#print "ACL Line Count = " + str(accessListCount)


def main():
	
	
	#PYSVN RELATED
	def ssl_server_trust_prompt(trust_dict ):
		retcode = True
		accepted_failures = trust_dict['failures']
		save = False 
		return retcode, accepted_failures, save
	
	def get_login(realm, username, may_save):
		try:
			svnRealm = configParser.get('SVNconfig','SVNrealm')
		except:
			print "Something bad happened when reading conf.ini SVNConfig section. Just throwing my hands up"
		retcode = True
		realm = svnRealm
		username = raw_input("Enter username: ")
		password = getpass.getpass()
		save = False
		return retcode,username,password,save
	
	def get_login2(realm, username, may_save):
		try:
			rancidUser = configParser.get('SVNconfig','SVNuser')
			rancidPassword = configParser.get('SVNconfig','SVNpassword')
			svnRealm = configParser.get('SVNconfig','SVNrealm')
		except:
			print "Something bad happened when reading conf.ini SVNConfig section. Just throwing my hands up"
		retcode = True
		realm = svnRealm
		username = rancidUser
		password = rancidPassword
		save = False
		return retcode,username,password,save
	
	
	
	
	configParser = SafeConfigParser()
	try:
		configParser.read('conf.ini')
		programMode = configParser.get('Basic','Mode')
		installedDir = configParser.get('Basic','InstalledDir')
		logDir = configParser.get('Basic','LogDir')
		tempDir = configParser.get('Basic','TempDir')
		outputDir = configParser.get('Basic','outputDir')
		DBhost = configParser.get('Database','DBhost')
		DBschema = configParser.get('Database','DBschema')
		DBuser = configParser.get('Database','DBuser')
		DBpassword = configParser.get('Database','DBpassword')
		
	except:
		print "Something bad happened when reading conf.ini. Failing to local mode"	
		programMode = 'Local'
	
	options = {}
	
	outputFile = outputDir+'output.txt'
	outputFileLargeACLs = outputDir+'output-LargeACLs.txt'
	outputFileLargeACLsForCopyAndPaste = outputDir+'output-LargeACLs-CopyPaste.txt'
	outputFileDebugDump = outputDir+'debugDump.txt'
	outputFileLogging = logDir+'LogFile.txt'
	
	
	
	
	options['DBhost'] = DBhost 	
	options['DBschema'] = DBschema
	options['DBuser'] = DBuser
	options['DBpassword'] = DBpassword
	
	#Based on programMode in conf.ini set or ask controlling variables.
	if programMode == 'All':
		debugDump = raw_input('do a debug dump? y/n :')
		if debugDump == 'y':
			doDebugDump = True
		else: doDebugDump = False
		pushToSQL = raw_input("Should I push data to SQL DB? y/n :")
		if pushToSQL == 'y':
			doSQLStuff = True
		else: doSQLStuff = False
		getFileFrom = raw_input("Where to get file from? local/remote/rancidlist : ")
	elif programMode == 'Local':
		debugDump = raw_input('do a debug dump? y/n :')
		if debugDump == 'y':
			doDebugDump = True
		else: doDebugDump = False
		getFileFrom = 'local'
		pushToSQL = False
	
	options['getFileFrom'] = getFileFrom
	options['doDebugDump'] = doDebugDump
	options['doSQLStuff'] = doSQLStuff 	
	
	
	
	# Based On set program control variables do some stuff
	if getFileFrom == 'local':
		input1 = raw_input("Enter local filename: ")
		inputFile = open(installedDir+input1 , 'r')
		options['deviceConfig'] = input1
		deviceType = raw_input("Enter Device Type[cisco_asa / cisco_switch: ")
		options['deviceType'] = deviceType
		deviceRepoRevisionNumber = 0 
	elif getFileFrom == 'remote':
		try:
			svnRepo = configParser.get('SVNconfig','SVNrepo')
		except:
			print "Something bad happened when reading conf.ini SVNconfig Section. Just throwing my hands up"
		#PYSVN Stuff
		deviceConfig = raw_input("Device IP Address: ")
		options['deviceConfig'] = deviceConfig
		deviceType = raw_input("Enter Device Type[cisco_asa / cisco_switch: ")
		options['deviceType'] = deviceType
		client = pysvn.Client()
		client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
		client.callback_get_login = get_login
		#Gets the Entire RepoList and Prints it out
		#repoList = client.list(svnRepo)
		##print dir(pysvn.depth)
		#print repoList
		#for x in repoList:
		#	for y in x:
		#		if y:
		#			print y["repos_path"]
		##Get Directory Revision Number
		#headRevision = client.revpropget("revision", url=svnRepo+deviceConfig)
		#clientInfo = client.info2(svnRepo+deviceConfig,revision=pysvn.Revision(pysvn.opt_revision_kind.head), recurse=False)
		#print clientInfo[0][1]['rev'].number
		rev = pysvn.Revision(pysvn.opt_revision_kind.head)
		info = client.info2(svnRepo+deviceConfig,revision=rev,recurse=False)
		revno = info[0][1].last_changed_rev.number
		#revno = info[0][1].rev.number # revision number as an integer
		print "lastChange Revision Number = " + str(revno)
		deviceRepoRevisionNumber = revno
		#Pull the device config into a temporary file for parsing
		client.export(svnRepo+deviceConfig, installedDir+"tempConfigFile"+deviceConfig+".tmp")
		inputFile = open(installedDir+"tempConfigFile"+deviceConfig+".tmp",'r')	
		outputFile = outputDir+deviceConfig+".txt"
	elif getFileFrom == "rancidlist":
		#Check a local file for a list of configs to download from the SVN Repo
		configListFile = open('configList.conf','r')
		deviceRepoRevisionNumber = 0
	#elif getFileFrom == "AUTO":
	#	inputFile = passedFromControlScript 	
	
	
	options['deviceRepoRevisionNumber'] = deviceRepoRevisionNumber
	options['outputFile'] = outputFile
	options['outputFileLargeACLs'] = outputFileLargeACLs
	options['outputFileLargeACLsForCopyAndPaste'] = outputFileLargeACLsForCopyAndPaste
	options['outputFileDebugDump'] = outputFileDebugDump
	options['outputFileLogging'] = outputFileLogging	
	
		
	
	
	#Parse the inputFile with the options from the dict
	if getFileFrom == 'local' or getFileFrom == 'remote':
		ParseMe(inputFile, options)
	if getFileFrom == 'rancidlist':
		try:
			svnRepo = configParser.get('SVNconfig','SVNrepo')
		except:
			print "Something bad happened when reading conf.ini SVNconfig Section. Just throwing my hands up"
		#Get a SVN Client connection
		client = pysvn.Client()
		client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
		#Get_login2 will pull the credentials for the conf.ini
		client.callback_get_login = get_login2
		print "Logged into SVN REPO"
		#Read the config list and start looping
		###configListLinesStripped = []
		configListLines = configListFile.readlines()
		###strip newline characters and whitespace
		lineSplit = []
		#hostList = []
		
		#hostListType = []
		#for line in configListLines:
		#	lineSplit = line.split()
		#	hostList.append(lineSplit[0])
		#	hostListType.append(lineSplit[1])
			#configListLinesStripped.append(line.strip())
		###for line in configListLinesStripped:
		print "----====Start Reading Through Device List====----"
		for line in configListLines:
			print "--Start Device"
			lineSplit = line.split()
			device = lineSplit[0]
			deviceType = lineSplit[1]
			print device + " " + deviceType
			rev = pysvn.Revision(pysvn.opt_revision_kind.head)
			info = client.info2(svnRepo+device,revision=rev,recurse=False)
			revno = info[0][1].last_changed_rev.number
			#revno = info[0][1].rev.number # revision number as an integer
			print "lastChange Revision Number = " + str(revno)
			deviceRepoRevisionNumber = revno
			#Pull the device config into a temporary file for parsing
			client.export(svnRepo+device, tempDir+"tempConfigFile"+device+".tmp")
			tempConfigFile = tempDir+'tempConfigFile'+device+'.tmp'
			inputFile = open(tempConfigFile,'r')	
			outputFile = outputDir+device+".txt"
			outputFileLargeACLs = outputDir+device+'-output-LargeACLs.txt'
			outputFileLargeACLsForCopyAndPaste = outputDir+device+'-output-LargeACLs-CopyPaste.txt'
			outputFileDebugDump = outputDir+device+'-debugDump.txt'
			outputFileLogging = logDir+'LogFile.txt'
			options['deviceConfig'] = device
			options['outputFile'] = outputFile
			options['deviceRepoRevisionNumber'] = deviceRepoRevisionNumber
			options['outputFileLargeACLs'] = outputFileLargeACLs
			options['outputFileLargeACLsForCopyAndPaste'] = outputFileLargeACLsForCopyAndPaste
			options['outputFileDebugDump'] = outputFileDebugDump
			options['outputFileLogging'] = outputFileLogging
			options['deviceType'] = deviceType
			options['installedDir'] = installedDir
			#options['logDir'] = logDir
			#options['tempDir'] = tempDir
			ParseMe(inputFile,options)
	
main()









	