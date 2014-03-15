'''
Created on Jun 29, 2013

@author: MrEd
'''
class ServiceObject:
    protocol = 'unknown'
    operator = 'unknown'
    port = 'unknown' #NOT USED - marked for clean up
    dest_startRange = 'unknown'
    dest_stopRange = 'unknown'
    fullLine = 'unknown'   
    icmpType = 'unknown' 
    
    sourceIsOG = False
    source_operator = 'unknown'
    source_port = 'unknown'
    source_portIsOG = False
    source_startRange = 'unknown'
    source_stopRange = 'unknown'
    
    destIsOG = False
    dest_operator = 'unknown'
    dest_port= 'unknown'
    dest_portIsOG = False
    
    name = 'unknown'
    
    
    
    def __init__(self,line):
        ruleSplit = line.split()
        
        if ruleSplit[0] == 'service-object':
            self.parseLine(line)
        elif ruleSplit[1] == 'service': 
            self.name = ruleSplit[2]
        elif ruleSplit[0] == 'protocol-object':
            self.protocol = ruleSplit[1]
        
    def parseLine(self,line):
        ruleSplit = line.split()
        self.protocol = ruleSplit[1] 
        indexLimit = len(ruleSplit) -1
        self.fullLine = line
        
        specialCase = False
        
        protoCols = 0
        
        sourcePortCols = 0
        
        destPortCols = 0
        basePos = 0
        # START PROCESSING PROTOCOL SECTION
        if not specialCase:
            if (ruleSplit[basePos+1] == 'tcp-udp' or ruleSplit[basePos+1] == 'tcp' or ruleSplit[basePos+1] == 'udp'):
                protoCols = 1
                
            if (ruleSplit[basePos+1] == 'object-group'):
                self.protocol = 'OBJECTGROUP'
                protoCols = 2
                self.protocolIsOG = True
            
            
            # START PROCESSING SOURCE PORT SECTION
            #Only Process If after the proto section the next word is source
            modBasePos = basePos+protoCols+1
            if (indexLimit > modBasePos):
                
                if (ruleSplit[modBasePos] == 'source'):
                    #print "STARTED SERVICE OBJECT SOURCE PORT SECTION"
                    if (ruleSplit[modBasePos+1] == 'object-group'):
                        sourcePortCols = 3
                        self.sourceIsOG = True
                        self.source = ruleSplit[modBasePos+2]
                    elif (ruleSplit[modBasePos+1] == 'lt' or ruleSplit[modBasePos+1] == 'gt' or ruleSplit[modBasePos+1] == 'eq' or ruleSplit[modBasePos+1] == 'neq'):
                        sourcePortCols = 3
                        self.source_operator = ruleSplit[modBasePos+1]
                        self.source_port = ruleSplit[modBasePos+1+1]
                    elif (ruleSplit[modBasePos+1] == 'range'):
                        sourcePortCols = 4
                        self.source_operator = ruleSplit[modBasePos+1]
                        self.source_startRange = ruleSplit[modBasePos+1+1]
                        self.source_stopRange = ruleSplit[modBasePos+1+1+1]
                    else:   #Assuming its a ICMP Type
                        sourcePortCols = 2
                        self.icmp_type = ruleSplit[modBasePos+1]
            
            #Process Dest Port Section 'lt | gt | eq | neq | range port number or range'
            modBasePos = basePos + protoCols + sourcePortCols + 1 
            if (indexLimit > modBasePos):
                if (ruleSplit[modBasePos] == 'destination' or 1 == 1):
                    #print "STARTED SERVICE OBJECT DEST PORT SECTION"
                    #Need to accoutn for Config lines that dont use "destination" in it
                    if ruleSplit[modBasePos] != 'destination':
                        modBasePos = modBasePos -1
                    if (ruleSplit[modBasePos+1] == 'object-group'):
                        destPortCols = 3
                        self.destIsOG = True
                        self.dest = ruleSplit[modBasePos+2]
                    elif (ruleSplit[modBasePos+1] == 'lt' or ruleSplit[modBasePos+1] == 'gt' or ruleSplit[modBasePos+1] == 'eq' or ruleSplit[modBasePos+1] == 'neq'):
                        destPortCols = 3
                        self.dest_operator = ruleSplit[modBasePos+1]
                        self.dest_port = ruleSplit[modBasePos+1+1]
                    elif (ruleSplit[modBasePos+1] == 'range'):
                        destPortCols = 4
                        self.dest_operator = ruleSplit[modBasePos+1]
                        self.dest_startRange = ruleSplit[modBasePos+1+1]
                        self.dest_stopRange = ruleSplit[modBasePos+1+1+1]
                    else:   #Assuming its a ICMP Type
                        destPortCols = 2
                        self.icmp_type = ruleSplit[modBasePos+1]
                    
        
        if specialCase:
            donothing = 1
            #print specialCaseType
        
        #WAS ORGINAL SECTION BUT HAD PROBELMS WITH NEW VERSION OF ASA CONFIGS
        #if self.protocol == 'tcp' or self.protocol == 'udp' or self.protocol == 'tcp-udp':
        #    self.operator = lineList[2]
        #    if self.operator == 'eq' or self.operator == 'gt' or self.operator=='lt' or self.operator=='neq':
        #        self.port = lineList[3]
        #    if self.operator == 'range':
        #        self.startRange = lineList[3]
        #        self.stopRange = lineList[4]
               
            
        if self.protocol == 'icmp' or self.protocol =='icmp6':
            if len(ruleSplit) > 2:
                self.icmpType = ruleSplit[2]
            
    def printVar(self):
        print "Name ", self.name
        print "Service Object ", self.protocol,self.icmpType,self.dest_operator,self.dest_port,self.dest_startRange,self.dest_stopRange        
        
    def printClean(self):
        buildString = 'service-object'
        if self.protocol != 'unknown':
            buildString = buildString + ' ' + self.protocol
        if self.icmpType != 'unknown':
            buildString = buildString + ' ' + self.icmpType
        if self.operator != 'unknown':
            buildString = buildString + ' ' + self.dest_operator
        if self.dest_port != 'unknown':
            buildString = buildString + ' ' + self.dest_port
        if self.startRange != 'unknown':
            buildString = buildString + ' ' + self.dest_startRange
        if self.stopRange != 'unknown':
            buildString = buildString + ' ' + self.dest_stopRange
        print buildString    
              
    def returnClean(self):
        buildString = ''
        if self.protocol != 'unknown':
            buildString = buildString + self.protocol
        if self.icmpType != 'unknown':
            buildString = buildString + ' ' + self.icmpType
        if self.operator != 'unknown':
            buildString = buildString + ' ' + self.dest_operator
        if self.dest_port != 'unknown':
            buildString = buildString + ' ' + self.dest_port
        if self.dest_startRange != 'unknown':
            buildString = buildString + ' ' + self.dest_startRange
        if self.dest_stopRange != 'unknown':
            buildString = buildString + ' ' + self.dest_stopRange
        return buildString    
    
    def returnProtocolAttributes(self):
        buildString = ''
        if self.protocol != 'unknown':
            buildString = buildString + self.protocol
        return buildString
    
    def returnDestPorts(self):
        buildString = ''
        if self.operator != 'unknown':
            buildString = buildString + ' ' + self.dest_operator
        if self.dest_port != 'unknown':
            buildString = buildString + ' ' + self.dest_port
        if self.dest_startRange != 'unknown':
            buildString = buildString + ' ' + self.dest_startRange
        if self.dest_stopRange != 'unknown':
            buildString = buildString + ' ' + self.dest_stopRange
        return buildString
    
    
                      
    def writeToDebugLog(self,outputFileDebugDump):        
        outputFileDebugDump.write("name="+self.name+" protocol="+self.protocol+" operator="+self.operator+" icmpType="+self.icmpType+"\n")
        outputFileDebugDump.write("destIsOG="+str(self.destIsOG)+" dest_operator="+self.dest_operator+" dest_port="+self.dest_port+" dest_portIsOG="+str(self.dest_portIsOG)+" dest_startRange="+self.dest_startRange+" dest_stopRange="+self.dest_stopRange+"\n")
        outputFileDebugDump.write("sourceIsOG="+str(self.sourceIsOG)+" source_operator="+self.source_operator+" source_port="+self.source_port+" source_portIsOG="+str(self.source_portIsOG)+" source_startRange="+self.source_startRange+" source_stopRange="+self.source_stopRange+"\n")                          
            
        
        
        
