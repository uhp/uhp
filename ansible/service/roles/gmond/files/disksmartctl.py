# !/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import subprocess
import sys, traceback, os

NAME_PREFIX = 'disk_smartctl_'
PARAMS = {
    'mounts': '/proc/mounts'
}

names = ['Power_On_Hours'
    , 'Runtime_Bad_Block'
    , 'UDMA_CRC_Error_Count'
    , 'Raw_Read_Error_Rate'
    , 'Seek_Error_Rate'
]

units ={'Power_On_Hours': 'Hours'
    , 'Runtime_Bad_Block': 'nums'
    , 'UDMA_CRC_Error_Count': 'nums'
    , 'Raw_Read_Error_Rate': '%'
    , 'Seek_Error_Rate': '%'
}

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
        return ('', 'Exception', 1,)


def open_mart(dev):
    out, err, code = execute('smartctl -s on %s' % dev)
    if code != 0:
        print('smartctl can not enable %s' % err)


def get_mounted_disks(lparams):
    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    with open(PARAMS['mounts'], 'r') as f:
        mounts = f.readlines()

    _devs = []
    devs = set()
    for mount in mounts:
        if mount.startswith('/dev/'):
            mount = mount.split()
            dev = mount[0]
            if os.path.islink(dev):
                dev = '/dev/%s' % os.readlink(dev).split('/')[-1]
            _devs.append(dev)

    for d in _devs:
        devs.add(d[0:8])

    return list(devs)


def get_value(name):
    """Return a value for the requested metric"""
    global DEVS

    _value = 'unknown'
  
    t = name.split("_")
    if len(t) < 3:
        return _value

    dev = "/dev/%s" % t[2]

    # use iostat to get the io stats
    (out, err, code,) = execute('smartctl -A %s' % dev)
    if code != 0:
        print("smartctl did not installed exit \n %s " % err)
        sys.exit(code)
    else:

        cleanedlines = []
        next_data = False
        for line in out.split('\n'):
            #This removes blank items from remaining list
            if next_data and line != '':
                cleanedlines.append(line)

            if line.startswith('ID#'):
                next_data = True

        current_dev = dev[5:]

        length = len(NAME_PREFIX + current_dev + '_')
        _current_name = name[length:]

        for l in cleanedlines:
            datas = l.split()

            if _current_name in datas:
                _value = datas[9]

    return float(_value)


def metric_init(lparams):
    """Initialize metric descriptors"""
    devs = get_mounted_disks(lparams)

    for dev in devs:
        open_mart(dev)

    global LPARAMS, DEVS
    LPARAMS = lparams
    DEVS = devs

    # parse devs and create descriptors
    descriptors = []
    for dev in devs:
        # use iostat to get the io stats
        (out, err, code,) = execute('smartctl -A %s' % dev)
        if code != 0:
            print("smartctl did not installed exit \n %s " % err)
            sys.exit(code)
        else:

            cleanedlines = []
            next_data = False
            for line in out.split('\n'):
                #This removes blank items from remaining list
                if next_data and line != '':
                    cleanedlines.append(line)

                if line.startswith('ID#'):
                    next_data = True

            current_dev = dev[5:]
            for l in cleanedlines:
                datas = l.split()
                current_name = datas[1]

                if current_name in names:
                    _name = NAME_PREFIX + current_dev + '_' + current_name

                    descriptors.append({
                        'name': _name,
                        'call_back': get_value,
                        'time_max': 60,
                        'value_type': 'float',
                        'units': units[current_name],
                        'slope': 'both',
                        'format': '%.0f',
                        'description': "iostat",
                        'groups': 'disk'
                    })

    return descriptors


def metric_cleanup():
    """Cleanup"""

    pass


# the following code is for debugging and testing
if __name__ == '__main__':
    descriptors = metric_init(PARAMS)

    for d in descriptors:
        print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name'])) + '  %s' % d['units']
