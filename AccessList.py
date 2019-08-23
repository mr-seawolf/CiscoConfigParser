'''
Created on Jul 22, 2013

@author: MrEd
'''
from  AccessListSubRule import *


class AccessList:
    name = 'unknown'
    listOfRules = []
    expandedRuleList = []
    accessListSubRuleList = [] #has broken down objects
        
    def __init__(self,lineList):
        self.name = lineList[1]
        self.listOfRules = []
        self.expandedRuleList = []
        self.accessListSubRuleList = []
        
    def printVar(self):
        print("ACL Name=",self.name," type=",self.type)
        
    def printClean(self):
        print("PRINT CLEAN")
        
    def printBareBones(self):
        print("PRINT BAREBONES")
    