#!/usr/bin/env python
# coding=utf-8

import database

ALARM_OK = "ok"
ALARM_WARN = "warn"
ALARM_ERROR = "error"
ALARM_CONFIG_ERROR = "config_error"

def get_cluster_name():
    cluster_name = ""
    session = database.getSession()
    cluster_name = database.get_service_conf(session,"ganglia","cluster_name")
    session.close()
    return cluster_name
