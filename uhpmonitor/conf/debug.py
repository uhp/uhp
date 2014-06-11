#!/usr/bin/python

import os
import sys
import json

f = open("port_key_flag.txt","r")

temp = f.read()

j = json.loads(temp)

all = {}
for (service,v) in j.items():
    for (role,v2) in v.items():
        ar = []
        for (name,value) in v2.items():
            ar.append('"%s__%s"' % (service,name) )
        #print '"%s":[%s],' % ( role, (",".join(ar)))
            print '"%s__%s"' % (service,name)
