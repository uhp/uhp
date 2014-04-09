#!python
# coding=utf8

import sys
import logging
import subprocess
import os
import platform

if __name__ != "__main__":
    sys.exit(1)

DIR=os.path.split(os.path.realpath(sys.argv[0]))[0]
UHP_HOME=os.path.dirname(DIR)
VIRTUAL_ENV="%s/myvirtualenv" % UHP_HOME

os.chdir(UHP_HOME)

PATH=os.environ.get('PATH')
PATH="%s/Scripts%s%s" % (VIRTUAL_ENV, os.path.pathsep, PATH)
env={'VIRTUAL_ENV':VIRTUAL_ENV, 'PATH':PATH, 'PYTHONHOME':''}

#def cmd(cmd):             
#    logging.debug("ran command: [%s]" % cmd)
#    p = subprocess.Popen(cmd) 
#    p.wait()
#    logging.debug("run command end")
#    return p.returncode

if not os.path.isdir(VIRTUAL_ENV):
    subprocess.call('python lib/virtualenv-1.9.1.py --no-site-packages %s' % VIRTUAL_ENV)

PIP="%s/Scripts/pip" % VIRTUAL_ENV
PY="%s/Scripts/python" % VIRTUAL_ENV

coms=["snakemq",
    "sqlalchemy",
    "tornado",    
    "threadpool",
    "callbacks",
    "mysql-python",
    "pyyaml",
    "lockfile"]

for com in coms:
    subprocess.call(PIP + ' install '+ com)
    
if platform.system() == "Linux":
    subprocess.call(PIP + ' install daemon')
    subprocess.call(PIP + ' install ansible')