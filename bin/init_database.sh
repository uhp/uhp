#!/bin/bash

action=$1

if [ "$action" == "create" ] 
then
    cd $UHP_HOME/uhpcommon ; ./database.py create_db
elif [ "$action" == "drop" ] 
then
    cd $UHP_HOME/uhpcommon ; ./database.py drop_db
elif [ "$action" == "init" ] 
then
    cd $UHP_HOME/uhpcommon ; ./database.py init
    cd $UHP_HOME/conf/ansible_var/ ; ./import_db_conf.py all
else
echo "init_database.py [action] "
echo "                 create: create all db table"
echo "                 init: import all default value"
echo "                 drop: drop all data"  
fi


#import os
#import logging
#import sys
#
#commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon")
#sys.path.append(commondir)
#
#import database
#
#def help():
#    print "init_database.py [action] "
#    print "                 create: create all db table"
#    print "                 init: import all default value"
#    print "                 clear: clear all data"  
#
#def create():
#    database.create_db()
#
#def clear():
#    database.drop_db()
#
#def init():
#    database.init()
#
#if __name__ == "__main__":  
#
#    if len(sys.argv) >= 2:
#        action = sys.argv[1]
#        print "running action: %s" % action
#        obj = locals()
#        print obj
#        if obj.has_key(action):
#            func = obj[action]
#            apply(func)
#        else:
#            help()
#    else:
#        help()
