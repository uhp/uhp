#!/usr/bin/env python

import string

from simpleparse.common import numbers, strings, comments
from simpleparse.parser import Parser
from lib.logger import log

class ExpParser():
    def __init__(self):
        declaration = r'''
        fun             :=  ( fun_name,'(',')' )/( fun_name,'(',exp_list,')' )
        fun_name        :=  [a-zA-Z0-9_-]+
        exp_list        :=  exp,(',',exp)*
        exp             :=  pm_exp
        pm_exp          :=  md_exp,('+'/'-',md_exp)*
        md_exp          :=  bracket_exp,('*'/'/',bracket_exp)*
        bracket_exp     :=  ('(',exp,')')/str_var/number
        str_var         :=  [a-zA-Z],[a-zA-Z0-9_=\\.]*
        '''
        self.fun_parser = Parser( declaration, "fun" )
        self.exp_parser = Parser( declaration, "exp" )

    def parse_exp(self, str):
        str = str.replace(" ","")
        success, child, nextcharacter = self.fun_parser.parse(str)
        if success == 1 :
            tag,start,end,subtags = child[0]
            func_name = str[start:end]
            exp_list = []
            if len(child) > 1 :
                tag,start,end,subtags = child[1]
                for exp in subtags:
                    exp_list.append(str[exp[1]:exp[2]])       
            return (func_name, exp_list)
        else:
            return (None,None)

    def get_exp_value(self, str, map):
        str = str.replace(" ","")
        success, child, nextcharacter = self.exp_parser.parse(str)
        if success == 1 :
            tag,start,end,subtags = child[0]
            return self._get_value(tag,start,end,subtags,str,map)
        else:
            return (None,"parse the exp %s failed" % str)

    def _get_value(self, tag,start,end,subtags,str,map):
        if tag == "number" :
            log.info("1")
            return (string.atof(str[start:end]),"")
        elif tag == "str_var" :
            temp = str[start:end]
            if map.has_key(temp) :
                #log.debug("get args %s %f" % (temp,map[temp]) )
                log.info("2")
                return (map[temp],"")
            else:
                log.info("3")
                return (None,"not find %s in map" % temp)
        elif tag == "exp" :
            for exp in subtags:
                log.info("4")
                return self._get_value(exp[0],exp[1],exp[2],exp[3],str,map)
        elif tag == "pm_exp" :
            re = None
            for exp in subtags:
                val,msg = self._get_value(exp[0],exp[1],exp[2],exp[3],str,map)
                if val != None :
                    if re == None:
                        re = val
                    else:
                        pos = exp[1]-1
                        op = str[pos:pos+1]
                        if op == '+' :
                            re = re + val
                        elif op == '-' :
                            re = re - val
                        else:
                            log.info("5")
                            return (None,"oper %s is not + or -" % op)
                        
                else:
                    log.info("6")
                    return (val,msg)
            log.info("7")
            return (re,"") 
        elif tag == "md_exp" :
            re = None
            for exp in subtags:
                val,msg = self._get_value(exp[0],exp[1],exp[2],exp[3],str,map)
                if val != None :
                    if re == None:
                        re = val
                    else:
                        pos = exp[1]-1
                        op = str[pos:pos+1]
                        if op == '*' :
                            re = re * val
                        elif op == '/' :
                            if val == 0.0:
                                return (None,"div value %s is 0 " % exp[0])
                            re = re / val
                        else:
                            log.info("8")
                            return (None,"oper %s is not * or /" % op)
                else:
                    log.info("9")
                    return (val,msg)
            log.info("10")
            return (re,"")
        else:
            if len(subtags) > 0 :
                for exp in subtags:
                    log.info("11")
                    return self._get_value(exp[0],exp[1],exp[2],exp[3],str,map)
            else:
                log.info("12")
                return (None,"unfind tag %s and have no subtags" % tag)
        
if __name__ == "__main__":   
    
    testData="rate((swap_total - swap_free) / mem_total * 5,(swap_total - swap_free) / 0.05,(swap_total - swap_free) * 0.2,a + b * c,(a + b) / c,a + b + c - b - c,a * b * c / a / b / c_.d_a-b-d_.d)"
    #testData="a()"
    
    ep = ExpParser()
    func_name,exp_list =  ep.parse_exp(testData)
    print func_name
    print exp_list
    import sys
    if func_name == None:
        sys.exit(1)
    map = {
    "swap_total":100,
    "swap_free":50,
    "mem_total":10,
    "a":10,
    "b":20,
    "c":30,
    "c_.d_a":1,
    "d_.d":1
    }
    for exp in exp_list:
        print ep.get_exp_value(exp,map)
    














