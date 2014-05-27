# !/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import subprocess
import sys, traceback, os

NAME_PREFIX = 'disk_iostat_'
PARAMS = {
    'mounts': '/proc/mounts'
}

names = ['rrqm_s'
    , 'wrqm_s'
    , 'r_s'
    , 'w_s'
    , 'rkB_s'
    , 'wkB_s'
    , 'avgrq_sz'
    , 'avgqu_sz'
    , 'await'
    , 'r_await'
    , 'w_await'
    , 'svctm'
    , 'util'
]

units = ['Queued Requests/s'
    , 'Queued Requests/s'
    , 'Requests/s'
    , 'Requests/s'
    , 'kB/s'
    , 'kB/s'
    , 'Sectors'
    , 'Sectors'
    , 'ms'
    , 'ms'
    , 'ms'
    , 'ms'
    , '%'
]

VALUES = {}

_PIPE = subprocess.PIPE


def execute(cmd):
    """
    execute the cmd and return back (stdout, stderr) output
    """
    try:
        p = subprocess.Popen(cmd, stdin=_PIPE, stdout=_PIPE, stderr=_PIPE, shell=True)
        out, err = p.communicate()
        code = p.returncode
        p.stdin.close()
        return (out, err, code,)
    except:
        pass


def get_mounted_disks(lparams):
    global VALUES

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    with open(PARAMS['mounts'], 'r') as f:
        mounts = f.readlines()

    devs = []
    for mount in mounts:
        if mount.startswith('/dev/'):
            mount = mount.split()
            dev = mount[0]
            if os.path.islink(dev):
                dev = '/dev/%s' % os.readlink(dev).split('/')[-1]
            devs.append(dev)
    return devs


def get_value(name):
    """Return a value for the requested metric"""
    global VALUES, LPARAMS, DEVS

    _value = 'unknown'

    for dev in DEVS:
        next_data = False
        # use iostat to get the io stats
        (out, err, code,) = execute('iostat -x -k -d %s' % dev)
        if code != 0:
            print("iostat did not installed exit \n %s " % err)
            sys.exit(code)
        else:

            for line in out.split('\n'):
                if next_data:
                    next_data = False
                    # split the data
                    datas = line.split()

                    current_dev = datas[0]
                    datas = datas[1:]

                    _value = float(datas[VALUES[name]])
                if line.startswith('Device:'):
                    next_data = True

    return _value


def metric_init(lparams):
    """Initialize metric descriptors"""
    devs = get_mounted_disks(lparams)
    global VALUES, LPARAMS, DEVS
    LPARAMS = lparams
    DEVS = devs

    # parse devs and create descriptors
    descriptors = []
    for dev in devs:
        next_data = False
        # use iostat to get the io stats
        (out, err, code,) = execute('iostat -x -k -d %s' % dev)
        if code != 0:
            print("iostat did not installed exit \n %s " % err)
            sys.exit(code)
        else:

            for line in out.split('\n'):
                if next_data:
                    next_data = False
                    # split the data
                    datas = line.split()

                    current_dev = datas[0]
                    datas = datas[1:]

                    for i in range(len(datas)):
                        _name = NAME_PREFIX + current_dev + '_' + names[i]
                        VALUES[_name] = i
                        descriptors.append({
                            'name': _name,
                            'call_back': get_value,
                            'time_max': 60,
                            'value_type': 'float',
                            'units': units[i],
                            'slope': 'both',
                            'format': '%f',
                            'description': "iostat",
                            'groups': 'disk'
                        })

                if line.startswith('Device:'):
                    next_data = True

    return descriptors


def metric_cleanup():
    """Cleanup"""

    pass


# the following code is for debugging and testing
if __name__ == '__main__':
    descriptors = metric_init(PARAMS)

    for i in range(9999):
        for d in descriptors:
            print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name'])) + '  %s' % d['units']
        print('-------------------------------------')
