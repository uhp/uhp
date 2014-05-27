#!/usr/bin/env python
# coding=utf-8

import database

ALARM_OK = "OK"
#same as alarmlist
ALARM_WARN = "WARN"
ALARM_ERROR = "ERROR"
ALARM_CONFIG_ERROR = "CONFIG_ERROR"

def get_cluster_name():
    cluster_name = ""
    session = database.getSession()
    cluster_name = database.get_service_conf(session,"ganglia","cluster_name")
    session.close()
    return cluster_name
