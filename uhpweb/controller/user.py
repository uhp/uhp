# -*- coding: UTF-8 -*-
import tornado
import static_config
import logging
import config
import json
from controller import BaseHandler
import util
import time

app_log = logging.getLogger("tornado.application")

class UserHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("user.html")
        
class UserBackHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self , path):
        if hasattr(self, path) :
            fun = getattr(self, path);
            if callable(fun):
                apply(fun)
        else:
            self.ret("error","unsupport action")
            
    @tornado.web.authenticated
    def post(self , path):
        self.get(path)
        
    def ret(self , status , msg , result={}):
        result["ret"] = status;
        result["msg"] = msg;
        self.write(tornado.escape.json_encode(result));
        
    def user(self):
        user = self.get_current_user();
        ret = {"user":user,"menus":static_config.usermenus}
        self.ret("ok", "", ret);
       
       
    def apprunning(self):
        url = ("http://%s:%s/ws/v1/cluster/apps?state=RUNNING" %(config.rmhost,config.rmport))
        runningApp = util.getHttpJson(url)
        queues = {}
        for app in runningApp["apps"]["app"]:
            queue = app["queue"]
            appid = app['id']
            if not queues.has_key(queue):
                queues[queue] = {}
            queues[queue][appid]=app
        ret={"queues":queues,"rmhost":config.rmhost,"rmport":config.rmport}
        self.ret("ok", "", ret);
   
            
    def applist(self):
        offset = self.get_argument("offset",0)
        limit = self.get_argument("limit",50)
        where = self.get_argument("where","1")
        orderField = self.get_argument("orderField","appid")
        orderDirection = self.get_argument("orderDirection","desc")
        
        #TODO
    def appsum(self):
        offset = self.get_argument("offset",0)
        limit = self.get_argument("limit",50)
        where = self.get_argument("where","1")
        orderField = self.get_argument("orderField","appid")
        orderDirection = self.get_argument("orderDirection","desc")
        
        #TODO
            