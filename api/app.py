import shlex
from flask import Flask, request, make_response, send_file, jsonify
import os
from .JWT import JWT
from .Drive import drive
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
        data = json.loads(request.data.decode("utf-8"))
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Responce.send(401, {}, "Username or password is missing")
        print(f"SELECT * FROM users WHERE username='{username}' AND password='{password}';")
        cur.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}';")
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
    print(f"Sign  Up: {data['username']} {data['password']} {data['email']}")
    cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (data['username'], data['email']))
    row = cur.fetchone()
    if row:
        if row[-1] == "pending":
            if row[4] != data['email']:
                return Responce.send(409, {}, "Username or email already used")    
            else:
                cur.execute(f"DELETE FROM users where userID ='{row[0]}';")
                cur.execute("DELETE FROM otp where userid =%s",(row[0],))
                con.commit()
        else :
            return Responce.send(409, {}, "Username or email already used")
    
    if "gmail.com" in data['email']:
        otp = random.randint(100000, 999999)
        try:
            if Mail.send_mail(data['email'], "Eduverse", f"{otp}",data["password"],data["username"]):
                userID = str(uuid.uuid4())
                cookie = JWT.encode({"data": str(userID)})
                cur.execute("INSERT INTO otp (userid, otp) VALUES (%s, %s)", (userID, otp))
                cur.execute("INSERT INTO users (userid, username, password, fullname, email, isadmin,status ) VALUES (%s, %s, %s, %s, %s, 'false', 'pending')",
                            (userID, data['username'], data['password'], data['fullname'], data['email']))
                con.commit()
                res = make_response(jsonify({"message": "OTP sent to email", "status_code": 200}))
                res.set_cookie("session", cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
                return res
        except:
            return Responce.send(500, {}, "Failed to send OTP, Please try again")
        return Responce.send(500, {}, "Server Error")
    else:
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
    try:
        print(f"SELECT * FROM pdfs WHERE pdf_path='{id}';")
        cur.execute(f"SELECT * FROM pdfs WHERE pdf_path='{id}';")
        row = cur.fetchone()
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Server error")
    if row:
        if "https://drive.google.com/file/d/" in row[0]:
            return Responce.send(200,{"path":f"{row[0]}"},"here is your file")
        else:
            return Responce.send(200,{"path":f"https://drive.google.com/file/d/{row[0]}/view"},"here is your file")
    else:
        return Responce.send(404, {}, "File not found")


@app.route("/api/v1/deletepdf/<id>", methods=["GET"])
def delpdf(id):
    con, cur = connectDB()
    if not id:
        return Responce.send(404, {}, "Not valid PDF")
    cookie = request.cookies.get("session")
    if cookie:
        try:
            decoded_cookie = JWT.decode(cookie)
            cur.execute("SELECT * FROM users WHERE userid=%s", (decoded_cookie['data'],))
            row = cur.fetchone()
            if row:
                cur.execute("SELECT * FROM pdfs WHERE pdf_path=%s",  (id,))
                row2 = cur.fetchone()
                if row2[4] == decoded_cookie["data"] or row[5]:
                    if drive.delete(row2[0]):
                        cur.execute("DELETE FROM bookmarks WHERE pdf_id=%s", (id,))
                        cur.execute("DELETE FROM pdfs WHERE pdf_path=%s", (id,))
                        con.commit()
                        return Responce.send(200, {}, "Deleted Successfully")
                    else:
                        return Responce.send(404, {}, "File not found")
                else:
                    return Responce.send(401, {}, "User not permitted to delete")
            else:
                return Responce.send(401, {}, "User is not authorized")
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
            print(f"select * from pdfs inner join users on pdfs.userid = users.userid where pdf_path IN('{pdf_ids}');")
            cur.execute(f"select * from pdfs inner join users on pdfs.userid = users.userid where pdf_path IN('{pdf_ids}');")
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
                return Responce.send(401,{},"Try Again")
        else:
            return Responce.send(422,{},"Missing OTP")
    else:
        return Responce.send(401,{},"requied filed not found")
    
@app.route("/api/v1/usercount", methods=["GET"])
def userCount():
    con,cur = connectDB()
    try:
        cur.execute("select COUNT(userid) from users;")
        row = cur.fetchone()
        if row:
            print(row)
            return Responce.send(200,{"user_count":row[0]},"User count")
        else:
            return Responce.send(500,{},"failed to count")
    except Exception as e:
        print(e)
        return Responce.send(500,{},"failed to count")
    
@app.route("/api/v1/allpdf", methods=["GET"])
def allPDF():
    con,cur = connectDB()

    userid = ''
    bookmarks = []
    try:
        cookie = request.cookies.get("session")
        print(f"Cookie: {cookie}")

        if cookie:
            try:
                decoded_cookie = JWT.decode(cookie)
                userid = decoded_cookie.get('data', '')
            except Exception as e:
                print(f"Error decoding cookie: {e}")

            if userid:
                try:
                    cur.execute("SELECT * FROM users WHERE userid=%s", (userid,))
                    row = cur.fetchone()

                    if row and row[0] == userid:
                        print("User ID:", userid)
                    else:
                        print("Error in decoding cookie")
                except Exception as e:
                    print(f"Error querying user: {e}")
                    return Responce.send(500, {}, "Server error")
            else:
                pass
        else:
            pass

    except Exception as e:
        print(f"Error: {e}")
        return Responce.send(500, {}, "Server error")

    try:
        cur.execute("""
            SELECT username, title, sub, sem, pdf_path, upload_date
            FROM pdfs
            INNER JOIN users ON pdfs.userid=users.userid
        """)
        rows = cur.fetchall()

        if not rows:
            return Responce.send(401, {}, "PDF not found with this data")
        if userid:
            cur.execute("SELECT pdf_id FROM bookmarks WHERE userid=%s", (userid,))
            bookmarks = [{row[0] for row in cur.fetchall()}]
        pdfs = []
        for row in rows:
            pdf_id = row[4].split(".")[0]
            pdf = {
                "username": row[0],
                "title": row[1],
                "subject": row[2],
                "Sem": row[3],
                "path": row[4],
                "date": row[5].strftime("%A-%d-%m-%y"),
                "isBookmarked": "true" if pdf_id in bookmarks else "false"
            }
            pdfs.append(pdf)
        return Responce.send(200, pdfs, "success")

    except Exception as e:
        print(f"Error: {e}")
        return Responce.send(500, {}, "Server trouble")

if __name__ == "__main__":
    app.run(debug=True)
