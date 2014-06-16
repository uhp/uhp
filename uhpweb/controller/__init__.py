# -*- coding: UTF-8 -*-
import tornado
import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

import config
import database
import static_config
from model.user import User

class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if not user: return None
        return  tornado.escape.json_decode(user)
    
    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user), expires_days=0.5)
        else:
            self.clear_cookie("user")
            
    def ret(self , status , msg , result={}):
        result["ret"] = status;
        result["msg"] = msg;
        self.write(tornado.escape.json_encode(result));

class LoginHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if user == None :
            self.render("login.html", title="uhp管理平台")
        else:
            self.login_jump(user['type'])

    def post(self):
        username = self.get_argument('useranme')
        password = self.get_argument('password')

        # valid: 强制密码修改为高强度口令（12位以上，需包括大小写字母和数字混合）
        def valid_passwd(pw):
            MIN_LEN = 12
            if(len(pw)<12):raise Exception("password too short, min length is %d" % MIN_LEN)
            has_A = False
            has_a = False
            has_0 = False
            for c in password:
                if not has_A and c >= 'A' and c <= 'Z':
                    has_A = True
                    continue
                if not has_a and c >= 'a' and c <= 'z':
                    has_a = True
                    continue
                if not has_0 and c >= '0' and c <= '9':
                    has_0 = True
                    continue
            if not has_A: raise Exception("password must at last has one upper char")
            if not has_a: raise Exception("password must at last has one little char")
            if not has_0: raise Exception("password must at last has one number char")

        valid_passwd(password)
        session = database.getSession()
        user = session.query(User).filter(and_(User.name == username, User.password == password)).first()
        session.close()
        if user:
            self.set_current_user({'name': user.name, 'password': user.password,"type": user.type })
            self.login_jump(user.type)
        else:
            self.redirect('/login')

    def login_jump(self, type):
        if type == 0 :
            self.redirect("/admin")
            return
            if config.install_manager:
                self.redirect("/admin")
            elif config.install_monitor:
                self.redirect("/monitor")
            else:
                self.redirect('/login')
        else:
            self.redirect("/user")

        
class UserHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("user.html")

class IndexHandler(BaseHandler):
    def get(self):
        self.redirect('/login')

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")
