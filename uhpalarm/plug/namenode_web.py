#!/usr/bin/env python
#coding=utf8

import os.path, logging, sys
import re
import StringIO
import string
from lxml import etree

#for main run
commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)

import util

def namenode_web(hosts,port):
    checker = NamenodeChecker()
    return checker.namenode_web(hosts,port)

class NamenodeChecker():

    def __init__(self):
        self.state = "OK"
        self.msg = u""
        self.msg_count = 1

    def update_msg(self,msg):
        self.msg += "%d: %s" % (self.msg_count, msg)
        self.msg_count = self.msg_count + 1

    def update_result(self, state, msg):
        if state == "ERROR" :
            self.state = state
            self.update_msg(msg)
        elif state == "WARN" :
            self.update_msg(msg)
            if self.state != "ERROR" :
                self.state = state

    def namenode_web(self,hosts,port):
        '''
        检查以下事项:
        1. namenode的storge目录的状态
        2. 各个datanode汇报的Failed Volumes 和最近心跳
        3. 两者的active状态
        4. 两者的tid
        '''
        ha_states = []
        tids = []
        for host in hosts:
            ha_state,tid = self.get_nm_and_check(host,port)
            ha_states.append(ha_state)
            tids.append(tid)
        
        self.check_ha_states(hosts, ha_states)
        self.check_tids(hosts, tids)
        
        return (self.state,self.msg)

    def check_ha_states(self, hosts, ha_states):
        h1 = hosts[0]
        h2 = hosts[1]
        s1 = ha_states[0]
        s2 = ha_states[1]
        if s1 == "active" and s2 == "active" :
            self.update_result("ERROR",u"检测到两个namenode都是active状态。")
        if s1 != "active" and s2 != "active" :
            self.update_result("ERROR",u"检测到两个namenode都不是active状态。")

    def check_tids(self, hosts, tids):
        diff = abs( tids[0]-tids[1] )
        if diff > 1000 :
            self.update_result("WARN",u"检测到两个namenode的TID相差%d。" % diff)
        elif diff > 10000 :
            self.update_result("ERROR",u"检测到两个namenode的TID相差%d。" % diff)

    def get_nm_and_check(self,host,port):

        url = "http://%s:%s/dfshealth.jsp" % (host,port)
        html = util.get_http(url,5)
        if html == None :
            self.update_result("ERROR",u"不能连接到%s:%s。" % (host,port) )
            return ("",0)
        #get ha_state tid
        ha_state = self.get_ha_state(html)
        tid = self.get_tid(html)
        #get storge 
        dirs = self.get_storge_dir(html)
        for (dir,dir_state) in dirs.items():
            if dir_state != "Active":
                self.update_result("ERROR",u"目录 %s 状态为 %s。" % (dir,dir_state) )

        #get live datanode status
        # {"name","pcremaining","volfails"}
        url = "http://%s:%s/dfsnodelist.jsp?whatNodes=LIVE" % (host,port)
        html = util.get_http(url,5)
        if html == None :
            self.update_result("ERROR",u"不能连接到%s:%s。" % (host,port) )
            return (ha_state,tid)

        tables = self.get_live_dn_table(html)
        for row in tables :
            if row["volfails"] > 0 :
                self.update_result("ERROR", u"机器 %s 检测到 %d 个损坏的卷。" % (row["name"],row["volfails"]) )
            if row["last_contact"] > 30 :
                self.update_result("ERROR", u"机器 %s 检测丢失心跳 %d秒。" % (row["name"],row["last_contact"]) )

        return (ha_state,tid)

    def get_ha_state(self, html):
        pattern = re.compile("<h1>NameNode '.*?' \((.*?)\)</h1>",re.S)
        m = pattern.search(html)
        if m :
            return m.group(1)
        return ""

    def get_tid(self, html):
        pattern = re.compile("<b>Current transaction ID:</b> (.*?)<br/>",re.S)
        m = pattern.search(html)
        if m :
            return int(m.group(1))
        return 0

    def get_storge_dir(self, html):
        pattern = re.compile('<table class="storage" title="NameNode Storage">.*?</thead>.*?</table>',re.S)
        m = pattern.search(html)
        result = {}
        if m :
            content =  m.group()
            return self.parse_storage_table(content)
        else:
            return result
    
    def parse_storage_table(self, html):
        result = {}
        table = etree.XML(html)
        rows = iter(table)
        for row in rows:
            values = [col.text for col in row]
            if len(values) > 2 :
                result[values[0]] = values[2]
        return result
    
    def get_live_dn_table(self, html):
        pattern = re.compile('<table class="nodes">.*</table>',re.S)
        m = pattern.search(html)
        if m :
            content = m.group()
            return self.parse_live_table(content)
        else:   
            return []
    
    def parse_live_table(self, html):
        '''
        解析table的html 返回一个完整的python table
        [{"col1":"val1","col2":"val2"}...]
        '''
        result = []
        parser = etree.HTMLParser()
        table   = etree.parse(StringIO.StringIO(html), parser)
    
        name_values = [ name.text for name in table.xpath("//table/tr/td[@class='name']/a")  ]
        #print name_values
    
        last_contact_values = [ int(last_contact.text) for last_contact in table.xpath("//table/tr/td[@class='lastcontact']")  ]
    
        pcremaining_values = [ string.atof(pcremaining.text) for pcremaining in table.xpath("//table/tr/td[@class='pcremaining`']") ]
        #print pcremaining_values
        
        volfails_values = [ int(volfails.text) for volfails in table.xpath("//table/tr/td[@class='volfails']") ]
        #print volfails_values
    
        max = len( name_values )
        index = 0 
        while index < max:
            row = {"name":name_values[index],"last_contact":last_contact_values[index]
                    ,"pcremaining":pcremaining_values[index],"volfails":volfails_values[index]}
            result.append(row)
            index = index + 1
        return result

if __name__ == "__main__":
    #print get_http("http://mob616:50088/ws/v1/cluster/apps?state=RUNNING")

    print namenode_web(["hadoop3","hadoop2"],"50070")

