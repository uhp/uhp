# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, String, Text, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref

class UHPBase():
    """Base class for uvpkeeper Models."""
    __table_args__ = {'mysql_engine': 'InnoDB','mysql_charset':'utf8'}




