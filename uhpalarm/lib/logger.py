#!/usr/bin/env python
# coding=utf-8

import logging
import logging.config

import config

logging.config.fileConfig("%s/uhp%s/conf/logging.conf" % (config.uhphome, "alarm"))
log = logging.getLogger("alarm")

