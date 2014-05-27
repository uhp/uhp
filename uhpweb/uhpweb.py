#!/usr/bin/env python
# coding:utf-8
import os.path, logging, sys

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from sqlalchemy import create_engine

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)
# commondir=os.path.join( os.getenv('UHP_HOME'),"uhpweb");
# sys.path.append(commondir)
import config
import database
from controller import *
from controller.monitor import *
from controller.admin import AdminHandler,AdminBackHandler
from controller.user import UserHandler,UserBackHandler
from controller import callback_lib

access_log = logging.getLogger("tornado.access")
app_log = logging.getLogger("tornado.application")
gen_log = logging.getLogger("tornado.general")
callback_log = logging.getLogger("callback.lib")

define("config", default='etc/uhpweb.conf', help="The uhpweb config file", type=str)
define("bind_host", default='0.0.0.0', help="The uhp-web bind host ip", type=str)
define("bind_port", default='59990', help="The uhp-web listening port", type=int)
define("logfile", default='uhpweb.log', help="The uhpweb log file name", type=str)
define("log_dir", default="logs", help="The uhpweb log dir", type=str)
define("logformatter", default='(%(name)s): %(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s', help="The uhpweb log formatter", type=str)

def parse_config_file(conf_file):
    conf_file = os.path.join( config.uhphome ,"uhpweb","etc","uhpweb.conf" )
    if os.path.exists(conf_file):
        options.parse_config_file(conf_file)
        gen_log.info("Load config file from %s" %(conf_file))
    else:
        gen_log.error("Cant load the config file from %s " % (conf_file))

def set_log(target_log, log_type):
    fileHandler = logging.FileHandler("%s/%s_%s" %(config.web_log_dir, log_type, config.web_log_file,))
    formatter = logging.Formatter(options.logformatter)
    fileHandler.setFormatter(formatter)
    target_log.addHandler(fileHandler)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/login", LoginHandler),
            (r"/admin", AdminHandler),
            (r"/user", UserHandler),
            (r"/monitorback/(.*)", MonitorBackHandler),
            (r"/adminback/(.*)", AdminBackHandler),
            (r"/userback/(.*)", UserBackHandler),
            (r"/logout", AuthLogoutHandler),
            (r'/statics/(.*)', tornado.web.StaticFileHandler, {'path':os.path.join(os.path.dirname(__file__), "statics")}),
            (r'/tmp/(.*)', tornado.web.StaticFileHandler, {'path':'/tmp'})
        ]
        settings = dict(
            app_title=u"uhpweb",
            template_path=os.path.join(os.path.dirname(__file__), "app"),
            static_path=os.path.join(os.path.dirname(__file__), "statics"),
            xsrf_cookies=False,
            cookie_secret="FS24FADSDSFDS$^&$$DJFHSJFDF",
            login_url="/login",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


def main(config_file):
    parse_config_file(config_file)
    set_log(access_log, "access")
    set_log(app_log, "app")
    set_log(gen_log, "gen")
    set_log(callback_log, "callback")
    
    #启动callback center
    callback_lib.begin()
    
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(config.web_bind_port, address=config.web_bind_host)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    options.parse_command_line(sys.argv)
    config_file = options.config
    main(config_file)
    
    
