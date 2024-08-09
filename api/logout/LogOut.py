from flask import request,make_response
from ResponceHandler import Responce
def process():
    try:
        res = make_response({"data":{},"message":"LogOut","status_code":200})
        res.set_cookie('session','', path='/', samesite='None', secure=True)
        return res
    except:
        return Responce.send(500,{},"server in truble")