import shlex
from flask import Flask, request, make_response, send_file, jsonify
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
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config["FRONT_END_URL"] = ""
app.config["POSTGRESQL_HOST"] = "ep-aged-rain-a472d7qt-pooler.us-east-1.aws.neon.tech"
app.config["POSTGRESQL_USER"] = "default"
app.config["POSTGRESQL_DB"] = "verceldb"
app.config["POSTGRESQL_PASSWORD"] = "2pVZitHFc5aY"

rootdir = os.getcwd()
pdfpath = os.path.join(rootdir, "api", "uploadpdf/")

def connectDB():
    try:
        con = psycopg2.connect(
            host=app.config["POSTGRESQL_HOST"],
            user=app.config["POSTGRESQL_USER"],
            password=app.config["POSTGRESQL_PASSWORD"],
            database=app.config["POSTGRESQL_DB"],
        )
        cur = con.cursor()
        return con, cur
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Error at server")

@app.route("/api/v1/login", methods=["POST"])
def login():
    con, cur = connectDB()
    try:
        cookie = request.cookies.get("session")
        if cookie:
            try:
                decoded_cookie = JWT.decode(cookie)
                cur.execute("SELECT * FROM users WHERE userid=%s", (decoded_cookie['data'],))
                row = cur.fetchone()
                if row:
                    if row[0] == decoded_cookie["data"]:
                        if row[-1] == "pending":
                            return Responce.send(402, {}, "Not verified user")
                        return Responce.send(200, {}, "Login successful")
            except Exception as e:
                print(e)
        
        data = json.loads(request.data.decode("utf-8"))
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Responce.send(401, {}, "Username or password is missing")
        
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        row = cur.fetchone()
        if row:
            if row[-1] == "pending":
                return Responce.send(402, {}, "Not verified user")
            payload = {"data": row[0]}
            jwt_cookie = JWT.encode(payload)
            if jwt_cookie:
                res = Responce.send(200, {}, "Authenticated Successfully")
                res.set_cookie('session', jwt_cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
                return res
            return Responce.send(500, {}, "Error in setting cookie")
        
        return Responce.send(401, {}, "Invalid username or password")
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Server error")

@app.route("/api/v1/signup", methods=["POST"])
def signup():
    con, cur = connectDB()
    data = json.loads(request.data.decode("utf-8"))
    
    if not all(key in data for key in ['username', 'fullname', 'password', 'email']):
        return Responce.send(405, {}, "Body should contain username, password, fullname, and email")
    
    if len(data['username']) < 5:
        return Responce.send(401, {}, "Username is too short")
    if len(data['password']) < 8:
        return Responce.send(401, {}, "Password is too short")
    if len(data['fullname']) < 8:
        return Responce.send(401, {}, "Full name is too short")
    if len(data['email']) < 8:
        return Responce.send(401, {}, "Email is too short")

    cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (data['username'], data['email']))
    row = cur.fetchone()
    if row:
        if row[-1] == "pending":
            if row[4] != data['email']:
                return Responce.send(409, {}, "Username or email already used")    
            else:
                cur.execute('DELETE FROM users where userID =%s',row[0])
                cur.execute("DELETE FROM otp where userid =%s",(row[0],))
                con.commit()
        else :
            return Responce.send(409, {}, "Username or email already used")
    
    if "gmail.com" in data['email']:
        otp = random.randint(100000, 999999)
        if Mail.send_mail(data['email'], "Eduverse", f"{otp}",row[2],row[1]):
            userID = str(uuid.uuid4())
            cookie = JWT.encode({"data": str(userID)})
            cur.execute("INSERT INTO otp (userid, otp) VALUES (%s, %s)", (userID, otp))
            cur.execute("INSERT INTO users (userid, username, password, fullname, email, isadmin,status ) VALUES (%s, %s, %s, %s, %s, 'false', 'pending')",
                        (userID, data['username'], data['password'], data['fullname'], data['email']))
            con.commit()
            res = make_response(jsonify({"message": "OTP sent to email", "status_code": 200}))
            res.set_cookie("session", cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
            return res
        return Responce.send(500, {}, "Server Error")
    
    return Responce.send(401, {}, "Eduverse supports only Gmail addresses")

@app.route("/api/v1/upload", methods=["POST"])
def upload():
    con, cur = connectDB()
    return uploadpdf.UploadPdf(app, cur, con)

@app.route("/api/v1/getuser", methods=["GET", "OPTIONS"])
def getuser():
    con, cur = connectDB()
    return GetUser.process(cur)

@app.route("/api/v1/logout", methods=["GET"])
def logout():
    return LogOut.process()

@app.route("/api/v1/getpdf", methods=["GET"])
def getpdf():
    con, cur = connectDB()
    return GetPdf.process(cur)

@app.route("/api/v1/pdf/<id>", methods=["GET"])
def pdf(id):
    con, cur = connectDB()
    id = id.split('.')
    if len(id) == 2 and id[1] == 'pdf':
        fullpath = os.path.join(pdfpath, f"{id[0]}.pdf")
        if os.path.exists(fullpath):
            cur.execute("SELECT * FROM pdfs WHERE id=%s", (id[0],))
            row = cur.fetchone()
            return send_file(fullpath, as_attachment=True, download_name=f"{row[1]}-EduVerse.pdf")
        return Responce.send(404, {}, "File not found")
    return Responce.send(401, {}, "Invalid file name")

@app.route("/api/v1/deletepdf/<id>", methods=["GET"])
def delpdf(id):
    con, cur = connectDB()
    if not id:
        return Responce.send(404, {}, "Not valid PDF")
    
    cookie = request.cookies.get("session")
    id = id.split(".")[0]
    if cookie:
        try:
            decoded_cookie = JWT.decode(cookie)
            cur.execute("SELECT * FROM users WHERE userid=%s", (decoded_cookie['data'],))
            row = cur.fetchone()
            if row:
                cur.execute("SELECT * FROM pdfs WHERE userid=%s AND id=%s", (decoded_cookie['data'], id))
                row2 = cur.fetchone()
                if row2 or row[5] == 1:
                    fullpath = os.path.join(pdfpath, f"{id}.pdf")
                    if os.path.exists(fullpath):
                        cur.execute("DELETE FROM bookmarks WHERE pdf_id=%s", (id,))
                        cur.execute("DELETE FROM pdfs WHERE id=%s", (id,))
                        con.commit()
                        os.remove(fullpath)
                        return Responce.send(200, {}, "Deleted Successfully")
                    return Responce.send(404, {}, "File not found")
                return Responce.send(401, {}, "Invalid Cookie")
            return Responce.send(401, {}, "Invalid Cookie")
        except Exception as e:
            print(e)
            return Responce.send(500, {}, "Server Error")
    return Responce.send(401, {}, "Not Authenticated")

@app.route("/api/v1/bookmark/<pdfid>", methods=["GET"])
def bookmarks(pdfid):
    con, cur = connectDB()
    if not pdfid:
        return Responce.send(422, {}, "Invalid pdfid")
    
    pdfid = pdfid.split(".")[0]
    cookie = request.cookies.get("session")
    if cookie:
        try:
            decoded_cookie = JWT.decode(cookie)
            cur.execute("SELECT * FROM bookmarks WHERE pdf_id=%s AND userid=%s", (pdfid, decoded_cookie['data']))
            if cur.fetchone():
                return Responce.send(205, {}, "Already Bookmarked")
            cur.execute("INSERT INTO bookmarks (pdf_id, userid) VALUES (%s, %s)", (pdfid, decoded_cookie['data']))
            con.commit()
            return Responce.send(200, {}, "Bookmark updated")
        except Exception as e:
            print(e)
            return Responce.send(500, {}, "Server Error")
    return Responce.send(401, {}, "Not Authenticated")

@app.route("/api/v1/bookmarks", methods=["GET"])
def getbookmarks():
    con,cur = connectDB()
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
    con,cur = connectDB()
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
    con,cur = connectDB()
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
if __name__ == "__main__":
    app.run(debug=True)
