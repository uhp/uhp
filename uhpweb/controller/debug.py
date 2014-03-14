# -*- coding: UTF-8 -*-

from controller import BaseHandler

class DebugHandler(BaseHandler):
    def get(self):
        self.render("debug.html")
