#!/usr/bin/env python
# coding=utf-8

# @auth: zhaigy@ucweb.com
# @date: 2014-01-23

import sys
import os
import ConfigParser


'''
从目录中加载配置文件
'''
class Config(object):
  __conf_file = None

  def __init__(self, autoload=True):
    if autoload and os.path.isdir("./conf"):
      APP = os.path.splitext(os.path.basename(sys.argv[0]))[0]
      self.load("./conf/%s.conf" % APP)

  def __str__(self):
    strs = [] 
    for k, v in self.__dict__.items():
      if isinstance(v, Config):
        for kk, vv in v.__dict__.items():
          strs.append('%s.%s=%s' % (k, kk, vv))
      else:
        strs.append('%s=%s' % (k, v))

    return '\n'.join(strs)

  def __getitem__(self, key):
    """=self[key]"""
    return self.__dict__[key]

  def __setitem__(self, key, val):
    """self[key]="""
    self.__dict__[key] = val

  def __getattr__(self, name):
    """访问一个不存在的属性时 self.name # name 不存在"""
    return None

  def __contains__(self, value):
    """value in self"""
    return value in self.__dict__

  def load(self, conf_file):
    conf_file = os.path.abspath(conf_file)
    if conf_file == self.__conf_file: 
      return self
    self.__conf_file = conf_file

    cf = ConfigParser.ConfigParser()
    cf.read(conf_file)
    for section in cf.sections():
      self.__dict__[section] = Config(False)
      for name, value in cf.items(section):
        self.__dict__[section].__dict__[name] = value
    return self
