'''
Created on Jul 26, 2013

@author: MrEd
'''

class AccessListSubRule:
    protocol = 'unknown'   #ip tcp udp icmp networkobject 
    protocolIsOG = False
    protocolIsO = False
    fullLine = 'unknown'  #Doesnt exsist 
    accessListType = 'unknown'  #extended remark standard
    typeOfAccess = 'unknown' #permit deny
    source = 'unknown'
    sourceIsOG = False
    sourceIsO = False
    source_operator = 'unknown'
    source_port = 'unknown'
    source_portIsOG = False
    source_portIsO = False
    dest = 'unknown'
    destIsOG = False
    destIsO = False
    dest_operator = 'unknown'
    dest_port= 'unknown'
    dest_portIsOG = False
    dest_portIsO = False
    icmp_type = 'unkown'
    accessListName = 'unknown' 
    specialCaseType = 'unknown'
    protocol_expanded = []
    source_ip_expanded = []
    source_port_expanded = []
    dest_ip_expanded = []
    dest_port_expanded = []


        
    def __init__(self,line):
        ruleSplit = line.split()
        indexLimit = len(ruleSplit) -1
        self.fullLine = line
        if (indexLimit > 0):
            self.accessListName = ruleSplit[1]
        if (indexLimit > 1):
            self.accessListType = ruleSplit[2]
        specialCase = False
        if self.accessListType == 'remark':
            specialCase = True
            specialCaseType = 'remark'
        if ruleSplit[-1] == 'inactive':
            specialCase = True
            specialCaseType = 'inactive'
        if ruleSplit[2] == 'standard':
            specialCase = True
            specialCaseType = 'standard'
            self.accessListType = 'standard'
        self.typeOfAccess = ruleSplit[3]
        protoCols = 0
        sourceCols = 0
        destCols = 0
        destPortCols = 0
        basePos = 3
	sourcePortCols = 0
        
        # START PROCESSING PROTOCOL SECTION
        if not specialCase:
            if (ruleSplit[4] == 'ip' or ruleSplit[4] == 'tcp' or ruleSplit[4] == 'udp' or ruleSplit[4] == 'icmp'):
                protoCols = 1
            elif (ruleSplit[4] == 'object-group'):
                protoCols = 2
                self.protocolIsOG = True
            elif (ruleSplit[4] == 'object'):
                protoCols = 2
                self.protocolIsO = True
	    else:
		protoCols = 1            

	    self.protocol = ruleSplit[basePos+protoCols]
            
            # START PROCESSING SOURCE SECTION
            if (ruleSplit[basePos+protoCols+1] == 'any' or ruleSplit[basePos+protoCols+1] == 'any4'):
                sourceCols = 1
                self.source = ruleSplit[basePos+protoCols+1]
            elif (ruleSplit[basePos+protoCols+1] == 'host'):
                sourceCols = 2   
                self.source = ruleSplit[basePos+protoCols+1+1] + " 255.255.255.255"
            elif (ruleSplit[basePos+protoCols+1] == 'object-group'):
                sourceCols = 2
                self.sourceIsOG = True
                self.source = ruleSplit[basePos+protoCols+1+1]
            elif (ruleSplit[basePos+protoCols+1] == 'object'):
                sourceCols = 2
                self.sourceIsO = True
                self.source = ruleSplit[basePos+protoCols+1+1] 
            else:  #Assuming it now a Network Based source, Be nice to have a check if its a network IP
                sourceCols = 2
                self.source = ruleSplit[basePos+protoCols+1] + " " + ruleSplit[basePos+protoCols+1+1]
            
            #Process Source Port section 'lt | gt | eq | neq | range port number or range
            modBasePos = basePos + protoCols + sourceCols
            if (indexLimit > modBasePos):
                if (ruleSplit[modBasePos+1] == 'lt' or ruleSplit[modBasePos+1] == 'gt' or ruleSplit[modBasePos+1] == 'eq' or ruleSplit[modBasePos+1] == 'neq'):
                    sourcePortCols = 2
                    self.source_operator = ruleSplit[modBasePos+1]
                    self.source_port = ruleSplit[modBasePos+1+1]
				#Following 4 lines will NOT work. Left in to make sure I don't try to make it work.
                #elif (ruleSplit[modBasePos+1] == 'object-group'):
                #    sourcePortCols = 2
                #    self.source_portIsOG = True
                #    self.source_port = ruleSplit[modBasePos+1+1]
                elif (ruleSplit[modBasePos+1] == 'range'):
                    sourcePortCols = 3
                    self.source_operator = ruleSplit[modBasePos+1]
                    self.source_port = ruleSplit[modBasePos+1+1] + ruleSplit[modBasePos+1+1+1]
                #Not Good Here either.
		#else:   #Assuming its a ICMP Type
                #    sourcePortCols = 1
                #    self.icmp_type = ruleSplit[modBasePos+1]
            # FILL ME IN!
                
            #START PROCESSING DEST SECTION - Should be exactly the same as source processing
            modBasePos = basePos + protoCols + sourceCols + sourcePortCols
            if (indexLimit > modBasePos): 
                if (ruleSplit[modBasePos+1] == 'any' or ruleSplit[modBasePos+1] == 'any4' ):
                    destCols = 1
                    self.dest = ruleSplit[modBasePos+1]
                elif (ruleSplit[modBasePos+1] == 'host'):
                    destCols = 2   
                    self.dest = ruleSplit[modBasePos+1+1] + " 255.255.255.255"
                elif (ruleSplit[modBasePos+1] == 'object-group'):
                    destCols = 2
                    self.destIsOG = True
                    self.dest = ruleSplit[modBasePos+1+1]
                elif (ruleSplit[modBasePos+1] == 'object'):
                    destCols = 2
                    self.destIsO = True
                    self.dest = ruleSplit[modBasePos+1+1]
                else:  #Assuming it now a Network Based source, Be nice to have a check if its a network IP
                    destCols = 2
                    self.dest = ruleSplit[modBasePos+1] + " " + ruleSplit[modBasePos+1+1]
            
            #Process Dest Port Section 'lt | gt | eq | neq | range port number or range'
            modBasePos = basePos + protoCols + sourceCols + sourcePortCols + destCols
            if (indexLimit > modBasePos):
                if (ruleSplit[modBasePos+1] == 'lt' or ruleSplit[modBasePos+1] == 'gt' or ruleSplit[modBasePos+1] == 'eq' or ruleSplit[modBasePos+1] == 'neq'):
                    destPortCols = 2
                    self.dest_operator = ruleSplit[modBasePos+1]
                    self.dest_port = ruleSplit[modBasePos+1+1]
                elif (ruleSplit[modBasePos+1] == 'object-group'):
                    destPortCols = 2
                    self.dest_portIsOG = True
                    self.dest_port = ruleSplit[modBasePos+1+1]
                elif (ruleSplit[modBasePos+1] == 'range'):
                    destPortCols = 3
                    self.dest_operator = ruleSplit[modBasePos+1]
                    self.dest_port = ruleSplit[modBasePos+1+1] + ruleSplit[modBasePos+1+1+1]
                else:   #Assuming its a ICMP Type
                    destPortCols = 1
                    self.icmp_type = ruleSplit[modBasePos+1]
                    
        
        if specialCase:
            if specialCaseType == 'standard':
                self.typeOfAccess = ruleSplit[3]
                if len(ruleSplit) == 6:
                        self.source = ruleSplit[4] + " " + ruleSplit[5]
                if len(ruleSplit) == 5:
                        self.source = ruleSplit[4] + " 255.255.255.255"
            donothing = 1
            #print specialCaseType
        
        
    def writeToDebugLog(self,outputFileDebugDump): 
            outputFileDebugDump.write("accessListName ="+self.accessListName +" accessListType="+self.accessListType+" typeOfAccess="+self.typeOfAccess+" specialCaseType="+self.specialCaseType+"\n")
            outputFileDebugDump.write("protocol="+self.protocol+" protocolIsOG="+str(self.protocolIsOG)+" protocolIsO="+str(self.protocolIsO)+" icmp_type="+self.icmp_type+"\n")
            outputFileDebugDump.write("source="+self.source+" sourceIsOG="+str(self.sourceIsOG)+" sourceIsO="+str(self.sourceIsO)+" source_operator="+self.source_operator+" source_port="+self.source_port+" source_portIsOG="+str(self.source_portIsOG)+" source_portIsO"+str(self.source_portIsO)+"\n")
            outputFileDebugDump.write("dest="+self.dest+" destIsOG="+str(self.destIsOG)+" destIsO="+str(self.destIsO)+" dest_operator="+self.dest_operator+" dest_port="+self.dest_port+" dest_portIsOG="+str(self.dest_portIsOG)+" dest_portIsO"+str(self.dest_portIsO)+"\n")
	    outputFileDebugDump.write("protocol_expanded=")
	    outputFileDebugDump.writelines("%s " % x for x in self.protocol_expanded)
	    outputFileDebugDump.write("\n")
	    outputFileDebugDump.write("source_ip_expanded=")
	    outputFileDebugDump.writelines("%s " % x for x in self.source_ip_expanded)
	    outputFileDebugDump.write("\n")
	    outputFileDebugDump.write("source_port_expanded=")
	    outputFileDebugDump.writelines("%s " % x for x in self.source_port_expanded)
	    outputFileDebugDump.write("\n")
	    outputFileDebugDump.write("dest_ip_expanded=")
	    outputFileDebugDump.writelines("%s " % x for x in self.dest_ip_expanded)
            outputFileDebugDump.write("\n")
	    outputFileDebugDump.write("dest_port_expanded=")
	    outputFileDebugDump.writelines("%s " % x for x in self.dest_port_expanded)
	    outputFileDebugDump.write("\n")         
        
            
        
