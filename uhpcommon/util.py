#!python
# coding=utf8

import logging
import urllib2
import json
import threading
import re


def get_http(url , timeout = 10):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req ,None, timeout)
        html = response.read()
        return html
    except:
        # print "get exception while getting "+url;
        logger = logging.getLogger("main")
        logger.exception("get http error:"+url)
    return None

def get_http_json(url , timeout = 10):
    html = get_http(url, timeout)
    try:
        if html:
            return json.loads(html)
        else:
            return None
    except:
        return None
    return None

def look_like_ip(host):
    match = re.findall(r'\d+\.\d+\.\d+\.\d+', host)
    if match:
        return True;
    else:
        return False;

if __name__ == "__main__":
    print get_http("http://mob616:50088/ws/v1/cluster/apps?state=RUNNING")