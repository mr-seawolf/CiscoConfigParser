'''
Created on Jun 29, 2013

@author: MrEd


'''

from ConfigParser import SafeConfigParser 
#import pysvn
import getpass
#import MySQLdb
import re
import csv
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
from  TunnelGroupObject import *
from CryptoMapObject import *
from DeviceObject import *
from operator import pos
from copy import deepcopy

def ParseMe(inputFile, options):
	#This are the Commands for Cisco ASA Firewalls
	listOfCommands = ['hostname', 'name', 'interface', 'object-group', 'network-object', 'description', 'service-object', 'port-object', 'group-object', 'access-list', 'nat', 'static', \
					 'access-group', 'crypto','domain-name','protocol-object','icmp-object', 'object', 'subnet', 'host', 'service','tunnel-group','default-group-policy','ntp']
	listOfCiscoSwitchCommands = ['hostname', 'interface', 'switchport', 'spanning-tree', 'nat','ntp']
	StartOfNewCommandObject = True
	linesIgnored = 0
	linesProcessed = 0
	linesTotal = 0
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
	listOfTunnelGroups = []
	listOfCryptoMaps = []
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
	installedDir = options['installedDir']
	
	#This will return a list[] of a ACL line expanded to every combination. It can be rather large
	#list contains entries like: access-list outside_access_in extended permit tcp 192.168.101.0 255.255.255.0 10.150.130.144 255.255.255.255  eq https
	def ExpandRule(rule,listOfObjectGroups,listOfAccessLists):
		global tempObjectGroupExpanded
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
			for x in tempExpandedRules:
				ruleSplit = x.split()
				objectIndexLocation = 0
				for x in ruleSplit:
					if x == 'object':
						foundObject = True
						break
					objectGroupIndexLocation += 1	
		return tempExpandedRules
				
	
	def ExpandObjectGroup(name,listOfObjectGroups):
		listOfObjectGroups
		global tempObjectGroupExpanded
		#tempObjectGroupExpanded = []
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
		global tempObjectGroupExpanded
		#tempObjectGroupExpanded = []
		for x in listOfObjectGroups:
			if x.name == name:
				break
		tempObjectGroupExpanded = tempObjectGroupExpanded + x.returnProtocolAttributes()
		for y in x.listOfObjectGroups:
			ExpandObjectGroupForProtocolAttributes(y,listOfObjectGroups)
		return tempObjectGroupExpanded
	
	def ExpandObjectGroupForDestPorts(name,listOfObjectGroups):
		global tempObjectGroupExpanded
		#tempObjectGroupExpanded = []
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
		listOfTunnelGroups
		listOfCryptoMaps
		objectExists = False
		
		
		#Handle Command access-group
		if commandName == 'access-group':
			tempAccessGroup = AccessGroup(line)
			listOfAccessGroups.append(tempAccessGroup)
		
		#Handle Command network-object
		if commandName == 'network-object':
			if lineList[1] == 'host':
				#Check if a network-object host already exists
				for x in listOfHosts:
					if x.ipAddy == lineList[2] and x.subnet == '255.255.255.255':
						objectExists = True
						if currentOpenRootCommand == 'object-group':
							listOfObjectGroups[-1].listOfNetworkObjects.append(NetworkObject(lineList[1],lineList,line))
				if objectExists == False:
					listOfHosts.append(NetworkObject(lineList[1],lineList,line))
					networkObjectCount += 1
					if currentOpenRootCommand == 'object-group':
							listOfObjectGroups[-1].listOfNetworkObjects.append(NetworkObject(lineList[1],lineList,line))
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
			if currentOpenRootCommand == 'interface' and (len(lineList) > 1):
					if lineList[1] == 'mode':
						listOfInterfaces[-1].setSwitchportMode(lineList[2])
					if lineList[1] == 'access':
						if lineList[2] == 'vlan':
							listOfInterfaces[-1].setAccessVlan(lineList[3])
					if lineList[1] == 'voice':
						if lineList[2] == 'vlan':
							listOfInterfaces[-1].setVoiceVlan(lineList[3])	
		#Did not verify parsing with ASA docs, only with our configs
		elif commandName == 'tunnel-group':
			#Check if a tunnel-group object already exists with same peer ID
			for x in listOfTunnelGroups:
				if x.peer == lineList[1]:
					objectExists = True
				else:
					objectExists = False
			if objectExists == False:
				listOfTunnelGroups.append(TunnelGroupObject(line))
						
		elif commandName == 'default-group-policy':
			holder = 1+1
		elif commandName == 'crypto':
			holder = 1+1
		elif commandName == 'nat':
			natSourceInterface ='not-set'
			natDestInterface = 'not-set'
			natType = 'not-set'
			natTranslation ='not-set'
						
			if currentOpenRootCommand == 'object':
				#break down the line.
				#Common sample nat (sourceInt,destInt) static TranslatedNat
				natType = lineList[2]
				natTranslation = lineList[3]
				natLineNum = linesTotal
				tempStrip = lineList[1].strip('()')
				#print tempStrip
				tempSplit = tempStrip.split(',')
				#print tempSplit[0]
				#print tempSplit[1]
				natSourceInterface = tempSplit[0]
				natDestInterface = tempSplit[1]
				#We need to find what networkobject to apply these nats to
				currentOpenRootCommandLineList = currentOpenRootCommandLine.split()
				findObjectNamed = currentOpenRootCommandLineList[2]
				pos = 0
				for o in listOfHosts:
					if o.name == findObjectNamed:
						listOfHosts[pos].setNatSourceInterface(natSourceInterface)
						listOfHosts[pos].setNatDestInterface(natDestInterface)
						listOfHosts[pos].setNatType(natType)
						listOfHosts[pos].setNatTranslation(natTranslation)
						listOfHosts[pos].setNatLineNum(natLineNum)
					else:
						pos += 1	
						
		#This is for parsing static NATs in older ASA versions
		elif commandName == 'static':
			natSourceInterface ='not-set'
			natDestInterface = 'not-set'
			natType = 'not-set'
			natTranslation ='not-set'
			
			if currentOpenRootCommand == 'static':
				#break down the line.
				#Common sample static (dmz1,outside) 207.200.48.43 192.168.18.100 netmask 255.255.255.255
				natType = lineList[0]
				natTranslation = lineList[2]
				tempStrip = lineList[1].strip('()')
				#print tempStrip
				tempSplit = tempStrip.split(',')
				#print tempSplit[0]
				#print tempSplit[1]
				natSourceInterface = tempSplit[0]
				natDestInterface = tempSplit[1]
				#We need to find what networkobject to apply these nats to
				#This will be older ASA version so its most likely an IP, so lets look for that
				findObjectNamed = lineList[3]
				pos = 0
				for o in listOfHosts:
					if o.ipAddy == findObjectNamed:
						listOfHosts[pos].setNatSourceInterface(natSourceInterface)
						listOfHosts[pos].setNatDestInterface(natDestInterface)
						listOfHosts[pos].setNatType(natType)
						listOfHosts[pos].setNatTranslation(natTranslation)
						listOfHosts[pos].setNatLineNum(natLineNum)
					else:
						pos += 1
		elif commandName == 'ntp':
			#Temp ghetto job, dump to a file for ntp config lines
			outputNTPFile = open(installedDir+"NTPsettings", 'a')
			outputNTPFile.write(hostname[0]+" " + line)	
			
	#Fun stuff below here.
	
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
		global tempObjectGroupExpanded
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
		global tempObjectGroupExpanded
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
		
	def ExpandExtendedAclForObject(aclSubRule,listOfHosts,listOfObjectGroups,listOfServiceObjects):
		global tempObjectGroupExpanded
		list1 = []
		list2 = []
		list3 = []
		list4 = []
		list5 = []
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
		
		#Load lists 1-5 back into object
		aclSubRule.protocol_expanded = list1
		aclSubRule.source_ip_expanded = list2
		aclSubRule.source_port_expanded = list3
		aclSubRule.dest_ip_expanded = list4
		aclSubRule.dest_port_expanded = list5
	
	def PrintStandardAclForHuman(aclSubRule):
		outputFile.write(aclSubRule.fullLine)

	#Checks if an address is in a network, returns True or False	
	def addressInNetwork(ip,net):
    		ipaddr = struct.unpack('!L',socket.inet_aton(ip))[0]
    		netaddr,bits = net.split('/')
    		netaddr = struct.unpack('!L',socket.inet_aton(netaddr))[0]
    		netmask = ((1<<(32-int(bits))) - 1)^0xffffffff
    		return ipaddr & netmask == netaddr & netmask


	print "****************START PARSING CONFIG****************************"
	#START PARSING THE inputFile
	for line in inputFile:
		linesProcessed += 1
		linesTotal += 1
		lineList = line.split()
		#print line
		#print currentOpenRootCommand
		whiteSpace = len(line) - len(line.lstrip())
		#print whiteSpace
		if line == '\n':
			if doDebugDump:
				outputFileDebugDump.write("BLANK LINE!\n Line# "+str(linesTotal))
		elif '::' in line:
			if doDebugDump:
				outputFileDebugDump.write("has '::', could be IPV6 related. Line# "+str(linesTotal))
		elif len(lineList) == 0:
			if doDebugDump:
				outputFileDebugDump.write("LineList array is zero: Line# "+str(linesTotal))
		elif line[0] != ' ':
			currentWhiteSpaceLevel = 0
			currentOpenRootCommandLine = line
			currentOpenRootCommand = lineList[0]
			#print "NO Whitespace - Start of new command CWL=",currentWhiteSpaceLevel," ",line
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				linesTotal += 1
		elif whiteSpace > 0 and currentWhiteSpaceLevel == 0:
			currentWhiteSpaceLevel += 1
			currentOpenSubCommandLine = line
			currentOpenSubCommandLine = lineList[0]
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				linesTotal += 1
		
		elif whiteSpace > 0 and whiteSpace == previousLineWhiteSpace:
			currentWhiteSpaceLevel = currentWhiteSpaceLevel
			currentOpenSubCommandLine = line
			currentOpenSubCommandLine = lineList[0]
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				linesTotal += 1
	
		elif whiteSpace > 0 and whiteSpace > previousLineWhiteSpace:
			currentWhiteSpaceLevel += 1
			currentOpenSubSubCommandLine = line
			currentOpenSubSubCommandLine = lineList[0]
			if lineList[0] in listOfCommands and deviceType == 'cisco_asa':
				LineParser(lineList[0],lineList,line)
			elif lineList[0] in listOfCiscoSwitchCommands and deviceType == 'cisco_switch':
				LineParser(lineList[0],lineList,line)
			else:
				linesIgnored += 1
				linesTotal += 1
			#outputFileDebugDump.write("4th if CURRENT WHITE SPACE LEVEL= ", str(currentWhiteSpaceLevel) + "\n")
		previousLineWhiteSpace = whiteSpace		

	#Break down each AccessList Rule into object based Sub Rules
	for tempACL in listOfAccessLists:    #Each ACL 
		for ruleInACL in tempACL.listOfRules:		# each rule part of the ACL
			#print ruleInACL		
			tempSubRuleObject = AccessListSubRule(ruleInACL)
			tempACL.accessListSubRuleList.append(tempSubRuleObject)
	#ABOVE here is required code for processing a config
	
	#Break down ACL's and add into the aclSubRule objects. Similar to the SQL load or pretty human printing
	count = 0
	#Break down the objects from listOfAccessLists and back to the same objects
	for x in listOfAccessLists:
		for y in x.accessListSubRuleList:
			ExpandExtendedAclForObject(y,listOfHosts,listOfObjectGroups,listOfServiceObjects)

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
		outputFileDebugDump.write("=================------------------DUMP listOfTunnelGroups[]------------========================\n")
		for x in listOfTunnelGroups:
			x.writeToDebugLog(outputFileDebugDump)
	
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
		outputFileLargeACLsForCopyAndPaste.write('\n')
	
	print "Hostname = " + hostname[0]
	print "Lines Processed = " + str(linesProcessed)
	print "Lines Ignored = " + str(linesIgnored) 
	print "lines total = " + str(linesTotal)
	print "****************STOP PARSING CONFIG****************"
	return(listOfAccessGroups,listOfHosts,listOfObjectGroups,listOfServiceObjects,listOfPortObjects,listOfProtocolObjects,listOfIcmpObjects,listOfAccessLists,listOfInterfaces,listOfTunnelGroups)

def CompareProtocolExpandedLists(list1,list2):
	set1 = set(list1)
	set2 = set(list2)
	if set1 == set2:
		return 100
	else:
		return 0

def CompareSourceIpExpandedLists(list1,list2):
	set1 = set(list1)
	set2 = set(list2)
	if set1 == set2:
		return 100
	else:
		return 0
	
def CompareSourcePortExpandedLists(list1,list2):
	set1 = set(list1)
	set2 = set(list2)
	if set1 == set2:
		return 100
	else:
		return 0
		
def CompareDestIpExpandedLists(list1,list2):
	set1 = set(list1)
	set2 = set(list2)
	if set1 == set2:
		return 100
	else:
		return 0
		
def CompareDestPortExpandedLists(list1,list2):
	set1 = set(list1)
	set2 = set(list2)
	if set1 == set2:
		return 100
	else:
		return 0

def CompareRuleType(aceOne,aceTwo):
	if aceOne.typeOfAccess == aceTwo.typeOfAccess:
		return 100
	else:
		return 0

def printCopyAndPasteOfSingleObject(fileWrite,fileWriteDebug,object,boolean):
	doDebugDump = boolean
	fileReqObjectGroupDebugDump = fileWriteDebug
	fileReqObjectGroupCopyPaste = fileWrite
	y = object
	if doDebugDump == True:
		fileReqObjectGroupDebugDump.write("Name of retreived object " + y.name + "\n")
		fileReqObjectGroupDebugDump.write("fullLine of object: " + y.fullLine)
		fileReqObjectGroupDebugDump.write("listOfNetworkObjects Length: "+str(len(y.listOfNetworkObjects))+"\n")
		fileReqObjectGroupDebugDump.write("listOfServiceObjects Length: "+str(len(y.listOfServiceObjects))+"\n")
		fileReqObjectGroupDebugDump.write("listOfObjectGroups Length: "+str(len(y.listOfObjectGroups))+"\n")
		fileReqObjectGroupDebugDump.write("listOfIcmpObjects Length: "+str(len(y.listOfIcmpObjects))+"\n")
		fileReqObjectGroupDebugDump.write("listOfPortObjects Length: "+str(len(y.listOfPortObjects))+"\n")
		fileReqObjectGroupDebugDump.write("listOfProtocolObjects Length: "+str(len(y.listOfProtocolObjects))+"\n")
	fileReqObjectGroupCopyPaste.write(y.fullLine)
        if doDebugDump == True:
       		fileReqObjectGroupDebugDump.write(y.fullLine)
	if len(y.listOfNetworkObjects) > 0:
		for z in y.listOfNetworkObjects:
			fileReqObjectGroupCopyPaste.write(z.fullLine)
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write(z.fullLine)
	if len(y.listOfServiceObjects) > 0:
		for z in y.listOfServiceObjects:
			fileReqObjectGroupCopyPaste.write(z.fullLine)
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write(z.fullLine)
	if len(y.listOfIcmpObjects) > 0:
		for z in y.listOfIcmpObjects:
			fileReqObjectGroupCopyPaste.write(z.fullLine)
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write(z.fullLine)
	if len(y.listOfPortObjects) > 0:
		for z in y.listOfPortObjects:
			fileReqObjectGroupCopyPaste.write(z.fullLine)
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write(z.fullLine)
	if len(y.listOfProtocolObjects) > 0:
		for z in y.listOfProtocolObjects:
			fileReqObjectGroupCopyPaste.write(z.fullLine)
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write(z.fullLine)
	#Add Sub groups to the object group
	if len(y.listOfObjectGroups) > 0:
		for z in y.listOfObjectGroups:
			fileReqObjectGroupCopyPaste.write(" group-object "+z+"\n")
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write(" group-object "+z+"\n")
	#Must end in an exit for copy and past to work
	if doDebugDump == True:
		fileReqObjectGroupCopyPaste.write("exit\n")
		fileReqObjectGroupDebugDump.write("exit\n")
	
def printCopyAndPasteOfObject(name,allObjectGroups,allPrintedObjects,fileWrite,fileWriteDebug,doDebugDump):
	for x in allObjectGroups:
		if x.name == name:
			break
	#IF has object groups cycle through them.
	if len(x.listOfObjectGroups)>0:
		for t in x.listOfObjectGroups:
			for r in allObjectGroups:
				if r.name == t:
					printCopyAndPasteOfObject(t,allObjectGroups,allPrintedObjects,fileWrite,fileWriteDebug,doDebugDump)
	#elif : #Has no object groups so we hit bottom, so print me
	if name not in allPrintedObjects:
		printCopyAndPasteOfSingleObject(fileWrite,fileWriteDebug,x,doDebugDump)
		allPrintedObjects.add(name)
			




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
			import MySQLdb #If not libaries not available, we will crash
		else: doSQLStuff = False
		getFileFrom = raw_input("Where to get file from? local/remote/rancidlist/localcompare : ")
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
	if getFileFrom == 'localpoc':
                input1 = raw_input("Enter local filename: ")
                inputFile = open(installedDir+input1 , 'r')
                options['deviceConfig'] = input1
                deviceType = raw_input("Enter Device Type[cisco_asa / cisco_switch: ")
                options['deviceType'] = deviceType
                deviceRepoRevisionNumber = 0 
	if getFileFrom == 'localcompare':
		input1 = raw_input("Enter local filename one: ")
                inputFile = open(installedDir+input1 , 'r')
		options['deviceConfig'] = input1
		input2 = raw_input("Enter local filename two: ")
		secondInputFile = open(installedDir+input2 , 'r')
                options['deviceConfig2'] = input2
                deviceType = raw_input("Enter Device Type[cisco_asa / cisco_switch: ")
                options['deviceType'] = deviceType
                deviceRepoRevisionNumber = 0
	elif getFileFrom == 'remote':
		import pysvn #libaries better be available, or we will crash
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
	options['installedDir'] = installedDir
		
	#Parse the inputFile with the options from the dict
	if getFileFrom == 'local' or getFileFrom == 'remote':
		print "Running as local"
		ParseMe(inputFile, options)

        #Parse the inputFile with the options from the dict
        if getFileFrom == 'localpoc':
                import socket,struct
		print "Running as localPOC"
                listOfAccessGroups,listOfHosts,listOfObjectGroups,listOfServiceObjects,listOfPortObjects,listOfProtocolObjects,listOfIcmpObjects,listOfAccessLists,listOfInterfaces,listOfTunnelGroups = ParseMe(inputFile, options)
		#File to write out ACE config line and the POC to contact
		outputFileSubnetToPOC = outputDir+'SubnetToPOC.txt'
		fileSubnetToPOC = open(outputFileSubnetToPOC,'w')
		outputFileSubnetToPOCdebug = outputDir+'SubnetToPOCdebug.txt'
                fileSubnetToPOCdebug = open(outputFileSubnetToPOCdebug,'w')
		#Load in the CSV File
		with open('POC.csv') as csvfile:
			pocDict = csv.DictReader(csvfile)
			#for row in pocDict:
			#print(row['ip'], row['subnet'], row['poc'])
		

		#Will have to cycle through all the ACE's in the ACL's and lookup against the imported CSV file
		expandedSplit = []
		for acl in listOfAccessLists:
			for ace in acl.accessListSubRuleList:
				#Print out the ACE we are working on
				if doDebugDump == True:
					fileSubnetToPOCdebug.write(ace.fullLine+"\n")
				#For the Dest Section - Come back to this
				if doDebugDump == True:
					fileSubnetToPOCdebug.write("DEST SECTION LOOKUP\n")
				#print "*********\n"
				for x in ace.dest_ip_expanded:
					if doDebugDump == True:
                                                fileSubnetToPOCdebug.write(x+"\n")#TEMP THING
                                        expandedSplit = x.split()
                                        try:
                                                if expandedSplit[1] == "255.255.255.255":
                                                        if doDebugDump == True:
                                                                fileSubnetToPOCdebug.write("IT's A HOST!\n")
                                                if expandedSplit[1] != "255.255.255.255":
                                                        if doDebugDump == True:
                                                                fileSubnetToPOCdebug.write("IT's A SUBNET!\n")


                                        except IndexError:
                                                print "Index Error, skipping " + x
                                                if doDebugDump == True:
                                                        fileSubnetToPOCdebug.write("Can't Parse, skipping '" + x + "'\n")

				#For the Source Section
				if doDebugDump == True:
					fileSubnetToPOCdebug.write("SOURCE SECTION LOOKUP\n")
				for x in ace.source_ip_expanded:
					if doDebugDump == True:
						fileSubnetToPOCdebug.write(x+"\n")#TEMP THING
					expandedSplit = x.split()
					try:
						if expandedSplit[1] == "255.255.255.255":
							if doDebugDump == True:
								fileSubnetToPOCdebug.write("IT's A HOST!\n")
						if expandedSplit[1] != "255.255.255.255":
							if doDebugDump == True:
								fileSubnetToPOCdebug.write("IT's A SUBNET!\n")


					except IndexError:
						print "Index Error, skipping " + x
						if doDebugDump == True:
							fileSubnetToPOCdebug.write("Can't Parse, skipping '" + x + "'\n")
				#End of ACE processing
				if doDebugDump == True:
					fileSubnetToPOCdebug.write("-----------------------------------------------------\n")

	#Parse the inputFile with the options from the dict
	if getFileFrom == 'localcompare':
		print "Running as localcompare"
		#Line below is the orginal basic parse
		#ParseMe(inputFile, options)
		#Changing ParseMe to return multiple lists
 		listOfAccessGroups1,listOfHosts1,listOfObjectGroups1,listOfServiceObjects1,listOfPortObjects1,listOfProtocolObjects1,listOfIcmpObjects1,listOfAccessLists1,listOfInterfaces1,listOfTunnelGroups1 = ParseMe(inputFile, options)
                # Changing options for the second file outputs and inputs
		outputFile = outputDir+"SECOND-output.txt"
		outputFileLargeACLs = outputDir+'SECOND-output-LargeACLs.txt'
		outputFileLargeACLsForCopyAndPaste = outputDir+'SECOND-output-LargeACLs-CopyPaste.txt'
		outputFileDebugDump = outputDir+'SECOND-debugDump.txt'
		outputFileLogging = logDir+'SECOND-LogFile.txt'
		outputFileAclComparisonDebugDump = outputDir+'ACLComparisonDebug.txt'
		outputFileAclMatchList = outputDir+'ACL_Match_List.txt'
		outputFileAclNoMatchList = outputDir+'ACL_NO_Match_List.txt'
		outputFileAcl100MatchList = outputDir+'ACL_100_Match_List_Dump.txt'
		outputFileReqObjectGroupDebugDump = outputDir+'ReqObjectGroupDebug.txt'
		outputFileReqObjectGroupCopyPaste = outputDir+'ReqObjectGroupCopyPaste.txt'
		options['deviceConfig'] = input2
		#print options['deviceConfig']
		options['outputFile'] = outputFile
		options['deviceRepoRevisionNumber'] = deviceRepoRevisionNumber
		options['outputFileLargeACLs'] = outputFileLargeACLs
		options['outputFileLargeACLsForCopyAndPaste'] = outputFileLargeACLsForCopyAndPaste
		options['outputFileDebugDump'] = outputFileDebugDump
		options['outputFileLogging'] = outputFileLogging
		options['deviceType'] = deviceType
		options['installedDir'] = installedDir
		fileAclComparisonDebugDump = open(outputFileAclComparisonDebugDump,'w')
		fileAclMatchList = open(outputFileAclMatchList,'w')
		fileAclNoMatchList = open(outputFileAclNoMatchList,'w')
		fileAcl100MatchList = open(outputFileAcl100MatchList,'w')
		fileReqObjectGroupDebugDump = open(outputFileReqObjectGroupDebugDump,'w')
		fileReqObjectGroupCopyPaste = open(outputFileReqObjectGroupCopyPaste,'w')
		listOfAccessGroups2,listOfHosts2,listOfObjectGroups2,listOfServiceObjects2,listOfPortObjects2,listOfProtocolObjects2,listOfIcmpObjects2,listOfAccessLists2,listOfInterfaces2,listOfTunnelGroups2 = ParseMe(secondInputFile, options)		
		print "Count for listOfAccessGroups: ", len(listOfAccessGroups1)
		print "Count for listOfHosts: ", len(listOfHosts1)
		print "Count for listOfObjectGroups: ", len(listOfObjectGroups1)
		print "Count for listOfServiceObjects: ", len(listOfServiceObjects1)
		print "Count for listOfPortObjects: ", len(listOfPortObjects1)
		print "Count for listOfProtocolObjects: ", len(listOfProtocolObjects1)
		print "Count for listOfIcmpObjects: ", len(listOfIcmpObjects1)
		print "Count for listOfAccessLists: ", len(listOfAccessLists1)
		print "Count for listOfInterfaces: ", len(listOfInterfaces1)
		print "Count for listOfTunnelGroups: ", len(listOfTunnelGroups1)
		print "Count for listOfAccessGroups2: ", len(listOfAccessGroups2)
		print "Count for listOfHosts2: ", len(listOfHosts2)
		print "Count for listOfObjectGroups2: ", len(listOfObjectGroups2)
		print "Count for listOfServiceObjects2: ", len(listOfServiceObjects2)
		print "Count for listOfPortObjects2: ", len(listOfPortObjects2)
		print "Count for listOfProtocolObjects2: ", len(listOfProtocolObjects2)
		print "Count for listOfIcmpObjects2: ", len(listOfIcmpObjects2)
		print "Count for listOfAccessLists2: ", len(listOfAccessLists2)
		print "Count for listOfInterfaces2: ", len(listOfInterfaces2)
		print "Count for listOfTunnelGroups2: ", len(listOfTunnelGroups2)

		print "---===BEGIN ACL COMPARISON===---"
		
		primaryConfigACL = ''
		secondaryConfigACL = ''
		for x in listOfAccessLists1:
			primaryConfigACL = primaryConfigACL + x.name + " "
		for x in listOfAccessLists2:
			secondaryConfigACL = secondaryConfigACL + x.name + " "
		print("ACL Choices on Primary Config: " + primaryConfigACL)
		input3 = raw_input("Enter Primary Config ACL to compare with: ")
		print("ACL Choices on Secondary Config: " + secondaryConfigACL)
		input4 = raw_input("Enter Secondary Config ACL to compare against Primary: ")
		input5 = raw_input("Enter the value to append to conflict ace/objects: ")
		aceMatchList = []
		aceNoMatchList = []
		primaryACL = []
		secondaryACL = []
		for x in listOfAccessLists1:
			if x.name == input3:
				primaryACL = x
		for x in listOfAccessLists2:
			if x.name == input4:
				secondaryACL = x
				
		#TEMP REMOVE LATER
		#for aceOneTemp in primaryACL.accessListSubRuleList:
		#	print "(DUMP PRIMARY ACL)AceOneTemp= " + aceOneTemp.fullLine
		#for aceTwoTemp in secondaryACL.accessListSubRuleList:
		#	print "(DUMP SECONDARY ACL)AceTwoTemp= " + aceTwoTemp.fullLine	
		
		#Start comparing all the ACLs to each other	
		for aceOneTemp in primaryACL.accessListSubRuleList:
			#for aceTwoTemp in aceMatchList:
			#print "(outerloop)AceOneTemp= " + aceOneTemp.fullLine
			#GO AWAY for aceTwoTemp in aceNoMatchList:
			i = 0
			while i < len(aceNoMatchList):
				aceTwoTemp = aceNoMatchList[i]
				#print "(innerLoop)(aceNoMatchList)AceTwoTemp= " + aceTwoTemp.fullLine
				protocolCompareValue = CompareProtocolExpandedLists(aceOneTemp.protocol_expanded,aceTwoTemp.protocol_expanded)
				sourceIpCompareValue = CompareSourceIpExpandedLists(aceOneTemp.source_ip_expanded,aceTwoTemp.source_ip_expanded)
				sourcePortCompareValue = 100  #Forcing a match until I verify soure port extractions
				#sourcePortCompareValue = CompareSourcePortExpandedLists(aceOneTemp.source_port_expanded,aceTwoTemp.source_port_expanded) #STUB OR COMMENT THIS
				destIpCompareValue = CompareDestIpExpandedLists(aceOneTemp.dest_ip_expanded,aceTwoTemp.dest_ip_expanded)
				destPortCompareValue = CompareDestPortExpandedLists(aceOneTemp.dest_port_expanded,aceTwoTemp.dest_port_expanded)
				typeOfAccessCompareValue = CompareRuleType(aceOneTemp,aceTwoTemp)
				#Combine the values for a total match value
				totalMatchValue = (protocolCompareValue + sourceIpCompareValue + sourcePortCompareValue + destIpCompareValue + destPortCompareValue + typeOfAccessCompareValue) / 6
				if doDebugDump == True:
					fileAclComparisonDebugDump.write("---===ACL COMPARISON TESTING===---\n")
					fileAclComparisonDebugDump.write("*****COMPARING SUMMARY BELOW*****\n")
					fileAclComparisonDebugDump.write("I'M IN THE NO MATCH LIST\n")
					fileAclComparisonDebugDump.write("Primary Config ACE  : "+ aceOneTemp.fullLine)
					fileAclComparisonDebugDump.write("Secondary Config ACE: " + aceTwoTemp.fullLine)
					fileAclComparisonDebugDump.write("protocolCompareValue: " + str(protocolCompareValue) + "\n")
					fileAclComparisonDebugDump.write("sourceIpCompareValue: " + str(sourceIpCompareValue) + "\n")
					fileAclComparisonDebugDump.write("sourcePortCompareValue: " + str(sourcePortCompareValue) + "\n")
					fileAclComparisonDebugDump.write("destIpCompareValue: " + str(destIpCompareValue) + "\n")
					fileAclComparisonDebugDump.write("destPortCompareValue" + str(destPortCompareValue) + "\n")
					fileAclComparisonDebugDump.write("typeOfAccessCompareValue" + str(typeOfAccessCompareValue) + "\n")
					fileAclComparisonDebugDump.write("totalMatchValue" + str(totalMatchValue) + "\n")

				if totalMatchValue == 100:
					fileAcl100MatchList.write("******MATCHING PAIR BELOW*****\n")
					fileAcl100MatchList.write("Primary ACE  : "+ aceOneTemp.fullLine)
					fileAcl100MatchList.write("Secondary ACe: "+ aceTwoTemp.fullLine)
					#Do Match stuff. Move ACE from No Match list to Match list
					#print "MATCH!"
					aceMatchList.append(aceTwoTemp)
					aceNoMatchList.remove(aceTwoTemp)
					#DONT increment i
				elif totalMatchValue < 100:
					i += 1
					#print "NO MATCH!"
						#Do Nothing since its already in the No Match List
					1 == 1  #Just a placeholder
				else:
					i += 1
					#Do A default case
				#	print "DEFAULT CASE!"
					1 == 1  #Just a placeholder
			#for aceTwoTemp in secondaryACL.accessListSubRuleList: #Compare to the Starting list
			i = 0
			while i < len(secondaryACL.accessListSubRuleList):
				aceTwoTemp = secondaryACL.accessListSubRuleList[i]
				#print "(innerLoop)(secondarACL)AceTwoTemp= " + aceTwoTemp.fullLine
				protocolCompareValue = CompareProtocolExpandedLists(aceOneTemp.protocol_expanded,aceTwoTemp.protocol_expanded)
				sourceIpCompareValue = CompareSourceIpExpandedLists(aceOneTemp.source_ip_expanded,aceTwoTemp.source_ip_expanded)
				sourcePortCompareValue = 100  #Forcing a match until I verify soure port extractions
				#sourcePortCompareValue = CompareSourcePortExpandedLists(aceOneTemp.source_port_expanded,aceTwoTemp.source_port_expanded) #STUB OR COMMENT THIS
				destIpCompareValue = CompareDestIpExpandedLists(aceOneTemp.dest_ip_expanded,aceTwoTemp.dest_ip_expanded)
				destPortCompareValue = CompareDestPortExpandedLists(aceOneTemp.dest_port_expanded,aceTwoTemp.dest_port_expanded)
				typeOfAccessCompareValue = CompareRuleType(aceOneTemp,aceTwoTemp)
				#Combine the values for a total match value
				totalMatchValue = (protocolCompareValue + sourceIpCompareValue + sourcePortCompareValue + destIpCompareValue + destPortCompareValue + typeOfAccessCompareValue) / 6
				if doDebugDump == True:
					fileAclComparisonDebugDump.write("---===ACL COMPARISON TESTING===---\n")
					fileAclComparisonDebugDump.write("*****COMPARING SUMMARY BELOW*****\n")
					fileAclComparisonDebugDump.write("I'M IN THE SECONDARY LIST\n")
					fileAclComparisonDebugDump.write("Primary Config ACE   :"+ aceOneTemp.fullLine)
					fileAclComparisonDebugDump.write("Secondary Config ACE: " + aceTwoTemp.fullLine)
					fileAclComparisonDebugDump.write("protocolCompareValue: "+ str(protocolCompareValue) + "\n")
					fileAclComparisonDebugDump.write("sourceIpCompareValue: " + str(sourceIpCompareValue) + "\n")
					fileAclComparisonDebugDump.write("sourcePortCompareValue: " + str(sourcePortCompareValue) + "\n")
					fileAclComparisonDebugDump.write("destIpCompareValue: " + str(destIpCompareValue) + "\n")
					fileAclComparisonDebugDump.write("destPortCompareValue" + str(destPortCompareValue) + "\n")
					fileAclComparisonDebugDump.write("typeOfAccessCompareValue" + str(typeOfAccessCompareValue) + "\n")
					fileAclComparisonDebugDump.write("totalMatchValue" + str(totalMatchValue) + "\n")				
				if totalMatchValue == 100:
					fileAcl100MatchList.write("******MATCHING PAIR BELOW*****\n")
                                        fileAcl100MatchList.write("Primary ACE  : "+ aceOneTemp.fullLine)
                                        fileAcl100MatchList.write("Secondary ACE: "+ aceTwoTemp.fullLine)
					#print "MATCH!"
					#Do Match stuff. Move ACE from starting list to Match list
					aceMatchList.append(aceTwoTemp)
					secondaryACL.accessListSubRuleList.remove(aceTwoTemp)
				elif totalMatchValue < 100:
					#print "NO MATCH!"
					#Do NO Match stuff
					aceNoMatchList.append(aceTwoTemp)
					secondaryACL.accessListSubRuleList.remove(aceTwoTemp)
				else:
					i += 1
					#print "DEFAULT CASE!"
					#Do A default case
					1 == 1  #Just a placeholder
		
		print "ACE's in the Match List: ", len(aceMatchList)
		print "ACE's in the NO Match List: ", len(aceNoMatchList)
		print "ACE's in the secondaryACL List: ", len(secondaryACL.accessListSubRuleList)
		print "ACE's in the primaryACL: ", len(primaryACL.accessListSubRuleList)	
		#print "***aceMatchList***"
		fileAclMatchList.write("*** ACE MATCH LIST ***\n")
		for x in aceMatchList:
			#print x.fullLine
			fileAclMatchList.write(x.fullLine)
		#print "***aceNoMatchList***"
		fileAclNoMatchList.write("*** ACE NO MATCH LIST ***\n")
		for x in aceNoMatchList:
			#print x.fullLine	
			fileAclNoMatchList.write(x.fullLine)
#Go through the aceNoMatchList to find required Object Groups for a copy and paste config
		setOfRequiredObjects = set()
		for tempACE in aceNoMatchList:	
			#Check if Protocol section is an Object Group
			if tempACE.protocolIsOG == True:
				setOfRequiredObjects.add(tempACE.protocol)
			elif  tempACE.protocolIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjects.add(tempACE.protocol)
			#Check if Source section is an Object Group
			if  tempACE.sourceIsOG == True:
				setOfRequiredObjects.add(tempACE.source)
			elif  tempACE.sourceIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjects.add(tempACE.source)
			#Check if Source Port section is an Object Group
			if  tempACE.source_portIsOG == True:
				#DO SOMETHING
				setOfRequiredObjects.add(tempACE.source_port)
			elif  tempACE.source_portIsO == True:
				setOfRequiredObjects.add(tempACE.source_port)
			#Check if Dest section is an Object Group
			if  tempACE.destIsOG == True:
				#DO SOMETHING
				setOfRequiredObjects.add(tempACE.dest)
			elif  tempACE.destIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjects.add(tempACE.dest)
			#Check if Dest port is an Object Group
			if  tempACE.dest_portIsOG == True:
				#DO SOMETHING
				setOfRequiredObjects.add(tempACE.dest_port)
			elif  tempACE.dest_portIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjects.add(tempACE.dest_port)
		#print "REQUIRED OBJECTS"
		#for x in setOfRequiredObjects:
		 #print x

#x is just a name, so we have to retrieive the object from the listOfObjectGroups2
		allPrintedObjects = set()
		for x in setOfRequiredObjects:
			if doDebugDump == True:
				fileReqObjectGroupDebugDump.write("****Name of Object in Req List= "+x+"\n")
			printCopyAndPasteOfObject(x,listOfObjectGroups2,allPrintedObjects,fileReqObjectGroupCopyPaste,fileReqObjectGroupDebugDump,doDebugDump)

#Identify where objects fullLine do not match. This is name, not content
		setOfRequiredObjectsNameConflicts = set () #The ending tcp/udp/tcp-udp
		setOfRequiredObjectsNoNameConflicts = set () #Add to config with no issues
		setOfRequiredObjectsExactFullLineMatch = set ()
		setOfRequiredObjectsNotInPrimary = set()
		for x in setOfRequiredObjects: #x is not an object, just a name of an object
			#retrive that object from the list of objects for secondary config
			for z in listOfObjectGroups2:
				if x == z.name:
					break
			#now z is the object in question
			for y in listOfObjectGroups1:
				if y.fullLine == z.fullLine:
					setOfRequiredObjectsExactFullLineMatch.add(z)
				if y.name == z.name and y.fullLine != z.fullLine:
					setOfRequiredObjectsNameConflicts.add(z)		

		outputFileReqObjectsExactFullLineMatch = outputDir+'ReqObjectsExactFullLineMatch.txt'
		fileReqObjectsExactFullLineMatch = open(outputFileReqObjectsExactFullLineMatch,'w')
		outputFileReqObjectsExactFullLineMatchDebug = outputDir+'ReqObjectsExactFullLineMatchDebug.txt'
		fileReqObjectsExactFullLineMatchDebug = open(outputFileReqObjectsExactFullLineMatchDebug,'w')		
		allPrintedObjects = set()

		#Print all the objects in the secondary config that have match in the primary config
		fileReqObjectsExactFullLineMatch.write("All Objects in the Secondary config that have a match in the Primary based on fullLine value\n")
		if doDebugDump == True:
                	fileReqObjectsExactFullLineMatchDebug.write("All Objects in the Secondary config that have a match in the Primary based on fullLine value\n")
		for x in setOfRequiredObjectsExactFullLineMatch:
			if doDebugDump == True:
				fileReqObjectsExactFullLineMatchDebug.write("****Name of Object in Req List= "+x.fullLine)
			printCopyAndPasteOfObject(x.name,listOfObjectGroups2,allPrintedObjects,fileReqObjectsExactFullLineMatch,fileReqObjectsExactFullLineMatchDebug,doDebugDump)

		outputFileReqObjectsNameConflicts = outputDir+'ReqObjectsNameConflicts.txt'
		fileReqObjectsNameConflicts = open(outputFileReqObjectsNameConflicts,'w')
		outputFileReqObjectsNameConflictsDebug = outputDir+'ReqObjectsNameConflictsDebug.txt'
		fileReqObjectsNameConflictsDebug = open(outputFileReqObjectsNameConflictsDebug,'w')		
		allPrintedObjects = set()
		
		#Print all the objects in the secondary config that have a conflict in the primary config
                fileReqObjectsNameConflicts.write("All Objects in the Secondary config that have a name conflict in the Primary based on fullLine value\n")
                if doDebugDump == True:
                        fileReqObjectsNameConflictsDebug.write("All Objects in the Secondary config that have a name conflict in the Primary based on fullLine value\n")
		for x in setOfRequiredObjectsNameConflicts:
			if doDebugDump == True:
				fileReqObjectsNameConflictsDebug.write("****Name of Object in Req List= "+x.fullLine)
			printCopyAndPasteOfObject(x.name,listOfObjectGroups2,allPrintedObjects,fileReqObjectsNameConflicts,fileReqObjectsNameConflictsDebug,doDebugDump)	

		#Remove the Name conflicts from the setOfRequiredObjects and print out
		outputFileReqObjectGroupCopyPasteModified = outputDir+'ReqObjectGroupCopyPasteModified.txt'
		fileReqObjectGroupCopyPasteModified = open(outputFileReqObjectGroupCopyPasteModified,'w')
		outputFileReqObjectGroupCopyPasteModifiedDebug = outputDir+'ReqObjectGroupCopyPasteModifiedDebug.txt'
		fileReqObjectGroupCopyPasteModifiedDebug = open(outputFileReqObjectGroupCopyPasteModifiedDebug,'w')
		setOfRequiredObjectsModified = setOfRequiredObjects.copy()
		for x in setOfRequiredObjectsNameConflicts:
			setOfRequiredObjectsModified.remove(x.name)
		#x is just a name, so we have to retrieive the object from the listOfObjectGroups2
		allPrintedObjects = set()
		for x in setOfRequiredObjectsModified:
			if doDebugDump == True:
				fileReqObjectGroupCopyPasteModifiedDebug.write("****Name of Object in Req List= "+x+"\n")
			printCopyAndPasteOfObject(x,listOfObjectGroups2,allPrintedObjects,fileReqObjectGroupCopyPasteModified,fileReqObjectGroupCopyPasteModifiedDebug,doDebugDump)
	
#Go through the aceNoMatchList to find required Object Groups for a copy and paste config
		outputFileAclNoMatchListAppended = outputDir+'ACLNoMatchListAppended.txt'
		fileAclNoMatchListAppended = open(outputFileAclNoMatchListAppended,'w')
		appendedValue = input5
		#appendedValue = "-SECOND"
		setOfRequiredObjectsAppendedValue = set()
		for tempACE in aceNoMatchList:
			#Check if Protocol section is an Object Group
			if tempACE.protocolIsOG == True:
				setOfRequiredObjectsAppendedValue.add(tempACE.protocol+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.protocol+" ",tempACE.protocol+appendedValue+" ")
			elif  tempACE.protocolIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjectsAppendedValue.add(tempACE.protocol+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.protocol+" ",tempACE.protocol+appendedValue+" ")
			#Check if Source section is an Object Group
			if  tempACE.sourceIsOG == True:
				setOfRequiredObjectsAppendedValue.add(tempACE.source+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.source+" ",tempACE.source+appendedValue+" ")
			elif  tempACE.sourceIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjectsAppendedValue.add(tempACE.source+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.source+" ",tempACE.source+appendedValue+" ")
			#Check if Source Port section is an Object Group
			if  tempACE.source_portIsOG == True:
				#DO SOMETHING
				setOfRequiredObjectsAppendedValue.add(tempACE.source_port+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.source_port+" ",tempACE.source_port+appendedValue+" ")
			elif  tempACE.source_portIsO == True:
				setOfRequiredObjectsAppendedValue.add(tempACE.source_port+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.source_port+" ",tempACE.source_port+appendedValue+" ")
			#Check if Dest section is an Object Group
			if  tempACE.destIsOG == True:
				#DO SOMETHING
				setOfRequiredObjectsAppendedValue.add(tempACE.dest+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.dest+" ",tempACE.dest+appendedValue+" ")
			elif  tempACE.destIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjectsAppendedValue.add(tempACE.dest+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.dest+" ",tempACE.dest+appendedValue+" ")
			#Check if Dest port is an Object Group
			if  tempACE.dest_portIsOG == True:
				#DO SOMETHING
				setOfRequiredObjectsAppendedValue.add(tempACE.dest_port+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.dest_port+" ",tempACE.dest_port+appendedValue+" ")
			elif  tempACE.dest_portIsO == True:
				#DO SOMETHING, This might only matter before version 9
				setOfRequiredObjectsAppendedValue.add(tempACE.dest_port+appendedValue)
				tempACE.fullLine = tempACE.fullLine.replace(tempACE.dest_port+" ",tempACE.dest_port+appendedValue+" ")
			fileAclNoMatchListAppended.write(tempACE.fullLine)		

		outputFileReqObjectGroupCopyPasteAppended = outputDir+'ReqObjectGroupCopyPasteAppended.txt'
		fileReqObjectGroupCopyPasteAppended = open(outputFileReqObjectGroupCopyPasteAppended,'w')			
		outputFileReqObjectGroupCopyPasteAppendedDebug = outputDir+'ReqObjectGroupCopyPasteAppendedDebug.txt'
		fileReqObjectGroupCopyPasteAppendedDebug = open(outputFileReqObjectGroupCopyPasteAppendedDebug,'w')		
#Copy the objects in the listOfObjectGroups2 to a new list where the Object Groups have the appended value
		listOfObjectGroups2Appended = deepcopy(listOfObjectGroups2)
		print "Count for listOfObjectGroups2Appended: ", len(listOfObjectGroups2Appended)         		
#For all required objects to merge in, append identifier
		for x in listOfObjectGroups2Appended:
			x.fullLine = x.fullLine.replace(x.name,x.name+appendedValue)
			x.name = x.name+appendedValue
			#print x.listOfObjectGroups
			for i in range(0, len(x.listOfObjectGroups)):
    				x.listOfObjectGroups[i]=x.listOfObjectGroups[i]+appendedValue
			
		#for x in listOfObjectGroups2Appended:
		#	for y in x.listOfObjectGroups:
		#		y.name = y.name+appendedValue
#x is just a name, so we have to retrieive the object from the appended listOfObjectGroups2
		allPrintedObjects = set()
		for x in setOfRequiredObjectsAppendedValue:
			if doDebugDump == True:
				fileReqObjectGroupCopyPasteAppendedDebug.write("****Name of Object in Appended Require List= "+x+"\n")
			printCopyAndPasteOfObject(x,listOfObjectGroups2Appended,allPrintedObjects,fileReqObjectGroupCopyPasteAppended,fileReqObjectGroupCopyPasteAppendedDebug,doDebugDump)	


#Control stuff for text menu
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









	
