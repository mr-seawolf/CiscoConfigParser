CiscoConfigParser
=================

To parse though Cisco IOS and ASA configs to pull information out and into a text file or DB.

Zero Exception catching :)


WARNING-VIEW RAW TO LOOK AT CONFIG EXAMPLE.


Required configuration file in same location as main.py = conf.ini
[Basic]
#Mode Options
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

