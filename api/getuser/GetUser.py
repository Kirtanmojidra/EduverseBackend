from flask import request
from ..JWT import JWT
from ..Responcehandler import Responce
def process(cur):
    try:
        print("cookie")
        cookie = request.cookies.get("session")
        decoded_cookie = JWT.decode(cookie)
        print(decoded_cookie["data"])
        try:
            cur.execute(f"select * from users where userid='{decoded_cookie['data']}';")
            row = cur.fetchone()
            if row:
                if row[-1] == "pending":
                    return Responce.send(401,{},"User is not verified")
                return Responce.send(200,{"username":row[1],"fullname":row[3],"isadmin":row[5]},"")
            else:
                return Responce.send(401,{},"invalid user data")
        except Exception as e:
            print(f"Fetching Error: {e}")
            return Responce.send(500,{},f"server in truble {e}")
    except:
        return  Responce.send(401,{},"invalid cookie")
