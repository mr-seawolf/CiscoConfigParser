'''
Created on Nov 29, 2013

@author: MrEd
'''

class InterfaceObject:
    interface = 'unknown'
    accessVlan = 0
    voiceVlan = 0
    spanningtreePortfastEnabled = False
    switchportMode = 'unknown'
        
    def __init__(self,line):
        lineSplit = line.split()
        self.interface = lineSplit[1]
               
        
            
    def setAccessVlan(self,accessVlan):
        self.accessVlan = accessVlan
        
    def setVoiceVlan(self,voiceVlan):
        self.voiceVlan = voiceVlan
    
    def setSpanningtreePortfastEnabled(self,spanningtreePortfastEnabled):    
        self.spanningtreePortfastEnabled = spanningtreePortfastEnabled
        
    def setSwitchportMode(self,switchportMode):
        self.switchportMode = switchportMode
        
    def parseLine(self,line):
        lineSplit = line.split()

    def printVar(self):
        print("interface="+self.interface+" accessVlan="+str(self.accessVlan)+" voiceVlan="+str(self.voiceVlan)+" spanningtreePortfastEnabled="+str(self.spanningtreePortfastEnabled)+" switchportMode="+self.switchportMode)
    
    def writeToDebugLog(self,outputFileDebugDump):
        outputFileDebugDump.write("interface="+self.interface+" accessVlan="+str(self.accessVlan)+" voiceVlan="+str(self.voiceVlan)+" spanningtreePortfastEnabled="+str(self.spanningtreePortfastEnabled)+" switchportMode="+self.switchportMode+"\n")
        
    def printClean(self):
        print(self.interface)
        print(self.accessVlan)
        print(self.voiceVlan)
        print(self.spanningtreePortfastEnabled)
        print(self.switchportMode)
        
    def printBareBones(self):
        print(self.interface)
    
    def returnClean(self):
        return self.interface
        
