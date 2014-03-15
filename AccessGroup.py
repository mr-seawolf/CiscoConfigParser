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
        self.aclApplied = ruleSplit[1]
        self.direction = ruleSplit[2]
        self.interfaceAppliedTo = ruleSplit[4]