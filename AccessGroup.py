'''
Created on Aug 18, 2013

@author: mred
'''

class AccessGroup:
    aclApplied = 'unknown'
    direction = 'unknown'
    interfaceAppliedTO = 'unknown'
    
    def __init__(self,line):
        ruleSplit = line.split()
        if ruleSplit[2] == 'global':
            self.aclApplied = ruleSplit[1]
            self.direction = 'unknown'
            self.interfaceAppliedTo = 'global'
        else:
            self.aclApplied = ruleSplit[1]
            self.direction = ruleSplit[2]
            self.interfaceAppliedTo = ruleSplit[4]