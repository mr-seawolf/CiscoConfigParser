
4/14 the section of code for this function "def addressInNetwork(ip,net):" was taken from http://stackoverflow.com/questions/819355/how-can-i-check-if-an-ip-is-in-a-network-in-python by the handle named "Johnson".
I have NOT fully tested it but it appeared to work enough for my current purpose. Long term is to use the netaddr module, but coudn't right now.

4/1 - for the localcompare option I forgot to compare the required network/service objects to be merged with the orginal list in the primary firewall. Sure they would merge naturally into a live running ASA BUT there is an issue if service group objects ends in a tcp/udp/tcp-dup or not.
If this exists;
object-group service TESTGROUP-TCP  (You can add service-objects to this, NOT port-objects)
And you try to add this;
object-group service TESTGROUP-TCP tcp  (You can add port-objects to this, NOT service-objects)
This will happen;.. causing the following exit to exit the configuration mode
TESTASA(config)# object-group service TESTGROUP tcp
An object-group with the same id but different type (service) exists

3/18 - I'll be updating the section soon since its horriable and the code needs some explaining.

CiscoConfigParser
=================

To parse though Cisco IOS and ASA configs to pull information out and into a text file or DB.

Very little exception catching :)

WARNING-You MUST have values for all values in the confi.ini (even if they are gibberish)<br />
WARNING-The file needs to be Cisco formatted. Extra blank lines can be an issue. Some config backup programs add extra lines to the beginning or end of the file. Haven't gotten around to accounting for those issues.<br />

Required configuration file in same location as main.py = conf.ini
```
[Basic]
#Mode Options - Just use "All" for now. Work in progress
#All = Ask alot of questions
#Local = All Local All the time
Mode=All

#Directory Locations require a trailing slash
InstalledDir=C:\dev\Projects\CiscoConfigParser\
LogDir=C:\dev\Projects\CiscoConfigParser\logs\
TempDir=C:\dev\Projects\CiscoConfigParser\tempdir\
OutputDir=C:\dev\Projects\CiscoConfigParser\output\

[Database]
DBuser=exampleuser
DBpassword=examplepassword
DBhost=examplehost
DBschema=exampleschema

[SVNconfig]
SVNrealm=EXAMPLE.COM
SVNrepo=https://svn.example.com/example/CVS/networking/configs/
SVNuser=examplesvnuser
SVNpassword=examplesvnpassword
```
```

----------------------------------------------------------------------------------
Sample Run (Only input lines are shown below)
python main.py
do a debug dump? y/n :y
Should I push data to SQL DB? y/n :n
Where to get file from? local/remote/rancidlist/localcompare : localcompare
Enter local filename one: gwefwc2.txt
Enter local filename two: gwnfwc2.txt
Enter Device Type[cisco_asa / cisco_switch: cisco_asa
ACL Choices on Primary Config: outside-in inside-out netmgmt PCAP
Enter Primary Config ACL to compare with: outside-in
ACL Choices on Secondary Config: outside inside mgt PCAP
Enter Secondary Config ACL to compare against Primary: outside
Enter the value to append to conflict ace/objects: -MERGEDIN
------------------------------------------------------------------------------

Primary = The first file inputted and is the config you will be merging into.
Secondary = The second file inputted and is the config you will be merging from.

ACL_100_Match_List_Dump.txt
	A list of the ACEs that match (Content) between the 2 ACL's compared.
ACL_Match_List.txt
	A list of ACEs in the secondary that have a matching (by content) ACE in the primary.
ACL_NO_Match_List.txt
	List of ACEs in the secondary that have NO matching (by content) ACE in the primary. Minus the first line this is copy and pastable into a running config, granted the required objects already exist.
ACLNoMatchListAppended.txt
	List of ACEs in the secondary that have NO matching (by content) ACE in the primary. There is also a value (Manually inputted during runtime) that is appended to the end of every Object Group used in the ACEs. This is copy and pastable into a running config, granted the required objects already exist. The intent is to avoid accidently merging or modifying objects in the primary that are named the same but are used for something else.  
debugDump.txt	
	Print out of all the lists and objects created during the inital parsing of a configuration. if 'localcompare' option is used than this would be the primary firewall.
output.txt (Fun fact: this was the orginal reason for this tool)
	Prints out a human readable columnar formatted break down of all the ACEs for all the ACLs in a config. It will expand out any object groups and nested object groups. 
output-LargeACLs.txt
	Prints out an expanded list of all the ACEs across all the ACLs. Useful if your porting to another cisco device that doesn't support object-groups. Most cisco routers/switches don't.
output-LargeACLs-CopyPaste.txt
	Prints out an expanded list of all the ACEs across all the ACLs. But this time its in a format that you can copy and paste into a running config.
ReqObjectGroupCopyPaste.txt
	Prints out all the Object Groups that are required from the secondary config to make all the ACEs listed in ACL_NO_Match_List.txt valid. This is copy and pastable into a running config.
ReqObjectGroupNoExits.txt
	Same as above but without exit statements. NOT Copy and pastable into a running config.
ReqObjectGroupCopyPasteAppended.txt
	Prints out all the Object Groups(with an appended value) that are required from the secondary config to make all the ACEs listed in ACLNoMatchListAppended.txt valid. This is copy and pastable into a running config.
ReqObjectGroupNoExitsAppended.txt	
	Same as above but without exit statements. NOT Copy and pastable into a running config.
ReqObjectGroupCopyPasteAppendedDebug.txt
	Similar to ReqObjectGroupCopyPasteAppended.txt but with extra information and is NOT copy and pastable.
ReqObjectGroupCopyPasteModified.txt
	ReqObjectGroupCopyPaste.txt minus ReqObjectsNameConflicts.txt.
	Prints out all the Object Groups that are required from the secondary config to make all the ACEs listed in ACL_NO_Match_List.txt valid BUT minus the object groups in the output ReqObjectsNameConflicts.txt. This is copy and pastable into a running config. There is potential for object group name conflicts when it involves service or port objects. Refer to "Name Conflict Issue" below.
ReqObjectGroupNoExitsModified.txt
	Same as above but without exit statements. NOT Copy and pastable into a running config.
ReqObjectGroupCopyPasteModifiedDebug.txt
	Similar to ReqObjectGroupCopyPasteModifiedDebug.txt but with additional information and is NOT copy and pastable.
ReqObjectGroupDebug.txt
	Similar to ReqObjectGroupCopyPaste.txt but with additional information and is NOT copy and pastable.
ReqObjectsExactFullLineMatch.txt
	Print out of all the Objects in the secondary config that have a match in the primary based on fullLine value. Minus the first line this is copy and pastable. 'fullLine' is a variable for many of the objects that contains the full line from the configuration. Created to help identify potential "Name Conflict Issues" (see below) and to eventually compare like named objects to see if the content is vastly different. You don't want to misuse an object that was named the same but was created for a different reason.
ReqObjectsExactFullLineMatchNoExits.txt
	Same as above but without exit statements. NOT Copy and pastable into a running config.
ReqObjectsExactFullLineMatchDebug.txt
	Similar to ReqObjectsExactFullLineMatch.txt but with additional information and is NOT copy and pastable.
ReqObjectsNameConflicts.txt
	All Objects in the Secondary config that have a name conflict in the Primary based on fullLine value. Refer to "Name Conflict Issue" below. These are conflicts that must be resolved. if you attempted to paste these into a running config it would fail.
ReqObjectsNameConflictsNoExits.txt
	Same as above but without exit statements. NOT Copy and pastable into a running config.
ReqObjectsNameConflictsDebug.txt
	Similar to ReqObjectsNameConflicts.txt but with more information.
SECOND-debugDump.txt
	Print out of all the lists and objects created during the initial parsing of a configuration. if 'localcompare' option is used than this would be the secondary firewall.
SECOND-output.txt
	Prints out a human readable columnar formatted break down of all the ACEs for all the ACLs in a config. It will expand out any object groups and nested object groups. 
SECOND-output-LargeACLs.txt
	Prints out an expanded list of all the ACEs across all the ACLs. Useful if your porting to another cisco device that doesn't support object-groups. Most cisco routers/switches don't.
SECOND-output-LargeACLs-CopyPaste.txt
	Prints out an expanded list of all the ACEs across all the ACLs. But this time its in a format that you can copy and paste into a running config.



------------------------------------------------------------
"Name Conflict Issue". Both object groups below are valid but only one type can exist on a firewall. 
object-group service NAME-OF-OBJECT
	Can contain 'service-object' objects.
object-group service NAME-OF-OBJECT tcp
	Can contain 'port-object' objects.
ASA01/act(config)# object-group service NAME-OF-OBJECT
ASA01/act(config-service-object-group)# ?
  description     Specify description text
  group-object    Configure an object group as an object
  help            Help for service object-group configuration commands
  no              Remove an object or description from object-group
  service-object  Configure a service object

ASA01/act(config-service-object-group)# object-group service NAME-OF-OBJECT
ASA01/act(config-service-object-group)# ?
  description   Specify description text
  group-object  Configure an object group as an object
  help          Help for service object-group configuration commands
  no            Remove an object or description from object-group
  port-object   Configure a port object
------------------------------------------------------------
```
