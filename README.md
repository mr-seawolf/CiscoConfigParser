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
