#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from datetime import datetime
import time
import rrdtool
import types
import rrd_contants
import math

import config

class RrdWrapper(object):

    def __init__(self, rrd_rootdir, image_rootdir, cluster_name=''):
        super(RrdWrapper, self).__init__()
        self.rrd_rootdir = rrd_rootdir
        self.image_rootdir = image_rootdir
        self.cluster_name = cluster_name

    # see get_last
    def query_last(self, metricName, hostname="__SummaryInfo__", clusterName="__SummaryInfo__"):
        rrdfile_in = self.get_rrd_file_path(metricName, hostname=hostname, clusterName=clusterName)
        return self.get_last(rrdfile_in)

    def query(self, metricName, startTime, endTime='now', hostname="__SummaryInfo__", clusterName="__SummaryInfo__"):
        """ Get dictionary with proper data from given period of time and for given node

        :param startTime:
        :type startTime: datetime, int or str
        :param endTime:
        :type endTime: datetime, int or str
        :param metricName: Metric name.
        :type metricName: String
        :param hostname: Node's hostname.
        :type hostname: String
        :param clusterName: Cluster's name.
        :type clusterName: String
        :return:
        :rtype: Dict
        """

        if metricName is None:
            raise Exception("Null parameter %s", "metricName")

        if startTime is None:
            raise Exception("Null parameter %s", "startTime")

        if type(startTime) == type(datetime.now()):
            start = str(int(time.mktime(startTime.timetuple()) * 1000))
        elif isinstance(startTime, types.FloatType):
            start = str(int(startTime))
        else:
            start = startTime

        if type(endTime) == type(datetime.now()):
            end = str(int(time.mktime(endTime.timetuple()) * 1000))
        elif isinstance(endTime, types.FloatType):
            end = str(int(endTime))
        else:
            end = endTime

        if clusterName is None:
            filePath = os.path.join(self.rrd_rootdir, hostname, metricName + ".rrd")
        else:
            filePath = os.path.join(self.rrd_rootdir, clusterName, hostname, metricName + ".rrd")


        return self._fetch_data(filePath, start, end)


    def _fetch_data(self, rrdfile, startTime, endTime):
        """ Fetch data from RRD archive for given period of time.

        :param rrdObject: RRDclusterName
        :type rrdObject: String
        :type startTime: int
        :type endTime: int
        :return: Dictionary with data from RRD archive.
        :rtype: Dict
        """

        if not os.path.exists(rrdfile):
            raise Exception("RRD File not exists %s" % rrdfile)
        
        return rrdtool.fetch(rrdfile, "AVERAGE", "--start", startTime, "--end", endTime)

    def get_last(self, rrdfile):
        '''
        获取最近5分钟的数据,选取最新更新的。
        返回（时间戳，数值）的二元组
        如果,最近5分钟没有数据则返回None
        '''
        result = rrdtool.fetch(rrdfile, "AVERAGE", "--start", "-300s", "--end", "now")
        time_meta = result[0]
        data = result[2]
        last_ts = None
        last_value = None
        ts_iter = time_meta[0]
        index = 0
        for ts_iter in range( time_meta[0], time_meta[1], time_meta[2] ):
            if data[index][0] != None:
                last_ts = ts_iter
                last_value = data[index][0]
            index = index + 1

        return (last_ts, last_value)

    def get_info(self, rrdfile):
        #TODO: translate into human-redable output.
        return rrdtool.info(rrdfile)


    def get_rrd_file_path(self, metricName, hostname="__SummaryInfo__", clusterName="__SummaryInfo__"):
        """
        :return the rrd file path
        :param metricName:
        :param hostname:
        :param clusterName:
        :return:
        """
        filePath = os.path.join(self.rrd_rootdir, clusterName, hostname, metricName + ".rrd")
        return filePath

    def get_rrd_names(self, prefix, hostname="__SummaryInfo__", clusterName="__SummaryInfo__"):
        """
        get the rrd file names as list which match the prefix
        :param prefix:
        :param hostname:
        :param clusterName:
        :return:
        """
        names = []
        rrd_dirname = os.path.join(self.rrd_rootdir, clusterName, hostname)
        for name in os.listdir(rrd_dirname):
            if name.startswith(prefix) and name.endswith('.rrd'):
                names.append(name[:-4])
        return names

    def get_all_rrd_names(self, hostname="__SummaryInfo__", clusterName="__SummaryInfo__"):
        """
        get the rrd file names as list which match the prefix
        :param prefix:
        :param hostname:
        :param clusterName:
        :return:
        """
        names = []
        rrd_dirname = os.path.join(self.rrd_rootdir, clusterName, hostname)
        for name in os.listdir(rrd_dirname):
            if name.endswith('.rrd'):
                _name = name[:-4]
                names.append(_name)
        return names

    def get_metrics_names(self, prefix, hostname="__SummaryInfo__", clusterName="__SummaryInfo__"):
        """
        get the rrd file names as list which match the prefix
        :param prefix:
        :param hostname:
        :param clusterName:
        :return:
        """
        names = []
        rrd_dirname = os.path.join(self.rrd_rootdir, clusterName, hostname)
        for name in os.listdir(rrd_dirname):
            if name.endswith('.rrd'):
                _name = name[:-4]
                _name = _name.partition(prefix)[-1]
                names.append(_name)
        return names

    def get_image_path(self, image_name, hostname="__SummaryInfo__", clusterName="default_cluster"):
        """
        :return the rrd file path
        :param image_name:
        :param hostname:
        :param clusterName:
        :return:
        """
        filePath = os.path.join(self.image_rootdir, clusterName, hostname, image_name + ".svg")

        dirname = os.path.dirname(filePath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return str(filePath)

    def draw(self, image_path, title, rrd_lines, startTime, endTime='now'):
        """

        :param opts:
        :type list
        :return:
        """
        if image_path is None:
            raise Exception("Null parameter %s", "image_path")

        if startTime is None:
            raise Exception("Null parameter %s", "startTime")

        if type(startTime) == type(datetime.now()):
            start = str(int(time.mktime(startTime.timetuple()) * 1000))
        elif isinstance(startTime, types.FloatType):
            start = str(int(startTime))
        else:
            start = startTime

        if type(endTime) == type(datetime.now()):
            end = str(int(time.mktime(endTime.timetuple()) * 1000))
        elif isinstance(endTime, types.FloatType):
            end = str(int(endTime))
        else:
            end = endTime

        args = [image_path, '--start', start, '--end', end, '--alt-autoscale',  
                      '-A', '--imgformat', 'SVG', '--rigid', '-c', 'SHADEA%s' % rrd_contants.white, '-w', '450', '-h', '180',
                      '-c', 'SHADEB%s' % rrd_contants.white, '-c', 'FRAME%s' % rrd_contants.dark_blue, '-c',
                      'FONT%s' % rrd_contants.light_blue, '--slope-mode', '-c', 'ARROW%s' % rrd_contants.red, '-c',
                      'AXIS%s' % rrd_contants.dark_blue, '-c', 'BACK%s' % rrd_contants.white, '--interlaced',
                      '--font', 'TITLE:9:', '--font', 'AXIS:7:', '--font', 'LEGEND:6:', '--font', 'UNIT:7:',
                      '--alt-autoscale-max',
                      '-t', title]
        args.extend(rrd_lines)
        apply(rrdtool.graph,args)

def convert_to_xy(rrd_fetch):
    x=[]
    y=[]
    time_info, columns, rows = rrd_fetch
    start, end, interval = time_info
    cur = start
    for row in rows:
        cur += interval
        x.append(cur)
        y.append(row[0])
    
    return (x,y)

# 从指定rras中分析出精度取值
# rras: [ RRA:AVERAGE:0.5:4:120 ]
def parse_precision(rras):
    precisions = []
    for rra in rras:
        vs = rra.split(':')
        interval = int(vs[3])
        numb = int(vs[4])
        sec = 15 * interval * numb
        precisions.append(sec)
    return precisions

if __name__ == '__main__':
    rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)


    from datetime import datetime

    start = '-2h'
    end = 'now'
   
    #data=rrd_wrapper.query('load_one',start, end, hostname='hadoop5', clusterName='test_hadoop')
    data=rrd_wrapper.query('dfs.datanode.HeartbeatsNumOps',start, end, hostname='hadoop5', clusterName='test_hadoop')
    print data
    print convert_to_xy(data)
    #rrdfile_in = rrd_wrapper.get_rrd_file_path('bytes_in', hostname='hadoop5', clusterName='test_hadoop')
    #rrdfile_out = rrd_wrapper.get_rrd_file_path('bytes_out', hostname='hadoop5', clusterName='test_hadoop')
    #image_path = rrd_wrapper.get_image_path('llddd', hostname='hadoop5', clusterName='test_hadoop')

    #rrd_lines = ['DEF:input=%s:sum:AVERAGE' % rrdfile_in,  #定义一个DEF变量
    #             'LINE1:input#BB1D48:In traffic',          #使用一个DEF变量定义一个LINE1
    #             'CDEF:bytes_in=input,8,*',                #定义一个CDEF变量
    #             'COMMENT: ',                              #注释
    #             'GPRINT:bytes_in:MAX:MAX in traffic\: %6.2lf %Sbps', #标注格式

    #             'DEF:output=%s:sum:AVERAGE' % rrdfile_out,
    #             'LINE2:output#002A6B:Out traffic', 
    #             'CDEF:bytes_out=output,8,*',
    #             'COMMENT: ',
    #             'GPRINT:bytes_out:MAX:MAX out traffic\: %6.2lf %Sbps',
    #             ]

    #rrd_wrapper.draw(image_path, "网络流量", rrd_lines, '-1h')
    #print rrd_wrapper.get_last(rrdfile_in)






