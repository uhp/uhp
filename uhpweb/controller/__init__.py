# -*- coding: UTF-8 -*-
import tornado
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_

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
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")
            
    def ret(self , status , msg , result={}):
        result["ret"] = status;
        result["msg"] = msg;
        self.write(tornado.escape.json_encode(result));

class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html", title="uhp管理平台")

    def post(self):
        username = self.get_argument('useranme')
        password = self.get_argument('password')
        session = database.getSession()
        user = session.query(User).filter(and_(User.name == username, User.password == password)).first()
        session.close()
        if user:
            self.set_current_user({'name': user.name, 'password': user.password,"type": user.type })
            if user.type==0 :
                self.redirect("/monitor")
            else:
                self.redirect("/user")
        else:
            self.redirect('/login')
        

        
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
