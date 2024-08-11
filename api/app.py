import shlex
from flask import Flask, request, make_response, send_file, jsonify, g
import os
import json
import uuid
import random
import psycopg2
from flask_cors import CORS
from .JWT import JWT
from .logout import LogOut
from .getuser import GetUser
from .upload import uploadpdf
from .getpdf import GetPdf
from .Responcehandler import Responce
from .Mail import Mail

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["FRONT_END_URL"] = ""
app.config["POSTGRESQL_HOST"] = "ep-aged-rain-a472d7qt-pooler.us-east-1.aws.neon.tech"
app.config["POSTGRESQL_USER"] = "default"
app.config["POSTGRESQL_DB"] = "verceldb"
app.config["POSTGRESQL_PASSWORD"] = "2pVZitHFc5aY"

rootdir = os.getcwd()
pdfpath = os.path.join(rootdir, "api/uploadpdf/")

def get_db():
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(
                host=app.config["POSTGRESQL_HOST"],
                user=app.config["POSTGRESQL_USER"],
                password=app.config["POSTGRESQL_PASSWORD"],
                database=app.config["POSTGRESQL_DB"]
            )
        except Exception as e:
            print(f"Error connecting to database: {e}")
            g.db = None
    return g.db

def get_cursor():
    conn = get_db()
    if conn is not None:
        return conn.cursor()
    return None

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route("/api/v1/login", methods=["POST"])
def login():
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    try:
        data = {}
        cookie = request.cookies.get("session")
        if cookie:
            try:
                decoded_cookie = JWT.decode(cookie)
                cursor.execute(f"SELECT * FROM users WHERE userid='{decoded_cookie['data']}'")
                row = cursor.fetchone()
                if row:
                    if row[0] == decoded_cookie["data"]:
                        if row[len(row)-1] == "pending":
                            return Responce.send(402, {}, "Not verified user...")
                        else:
                            return Responce.send(200, {}, "Login successful")
                    else:
                        return Responce.send(401, {}, "Invalid user")
            except Exception as e:
                print(e)
                return Responce.send(401, {}, "Invalid cookie")

        data = json.loads(request.data.decode("utf-8"))
        username = data.get('username')
        password = data.get('password')
        if username and password:
            cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}';")
            row = cursor.fetchone()
            if row:
                if row[len(row)-1] == "pending":
                    return Responce.send(402, {}, "Not verified user...")
                if username == row[1] and password == row[2]:
                    payload = {"data": row[0]}
                    jwt_cookie = JWT.encode(payload)
                    if jwt_cookie:
                        res = Responce.send(200, {}, "Authenticated successfully")
                        res.set_cookie('session', jwt_cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
                        return res
                    else:
                        return Responce.send(500, {}, "Error setting cookie")
            return Responce.send(401, {}, "Invalid username or password")
        return Responce.send(401, {}, "Username or password missing")
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Server error")
    finally:
        cursor.close()

@app.route("/api/v1/signup", methods=["POST"])
def signup():
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    try:
        data = json.loads(request.data.decode("utf-8"))
        if not all(key in data for key in ('username', 'fullname', 'password', 'email')):
            return Responce.send(405, {}, "Missing required fields")

        if len(data['username']) < 5:
            return Responce.send(401, {}, "Username too short")
        if len(data['password']) < 8:
            return Responce.send(401, {}, "Password too short")
        if len(data['fullname']) < 8:
            return Responce.send(401, {}, "Fullname too short")
        if len(data['email']) < 8:
            return Responce.send(401, {}, "Email too short")

        cursor.execute(f"SELECT * FROM users WHERE username='{data['username']}' OR email='{data['email']}'")
        row = cursor.fetchone()
        if row:
            return Responce.send(409, {}, "Username or email already used")

        if "gmail.com" in data['email']:
            otp = random.randint(100000, 999999)
            mail = Mail.send_mail(data['email'], "Eduverse", f"{otp}")
            if mail:
                userID = uuid.uuid4()
                cookie = JWT.encode({"data": f"{userID}"})
                cursor.execute(f"INSERT INTO otp VALUES('{userID}', '{otp}');")
                cursor.execute(f"INSERT INTO users VALUES('{userID}', '{data['username']}', '{data['password']}', '{data['fullname']}', '{data['email']}', 'false', 'pending');")
                conn.commit()
                res = make_response(jsonify({"message": "OTP sent to email. Check now.", "status_code": 200}))
                res.set_cookie("session", cookie, path='/', max_age=60*60*48, samesite='None', secure=True)
                return res
            return Responce.send(500, {}, "Error sending OTP")
        return Responce.send(401, {}, "Only Gmail addresses are supported")
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Server error")
    finally:
        cursor.close()

@app.route("/api/v1/upload", methods=["POST"])
def upload():
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    return uploadpdf.UploadPdf(app, cursor, conn)

@app.route("/api/v1/getuser", methods=["GET", "OPTION"])
def getuser():
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    return GetUser.process(cursor)

@app.route("/api/v1/logout", methods=["GET"])
def logout():
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    return LogOut.process()

@app.route("/api/v1/getpdf", methods=["GET"])
def getpdf():
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    return GetPdf.process(cursor)

@app.route("/api/v1/pdf/<id>", methods=["GET"])
def pdf(id):
    conn = get_db()
    if conn is None:
        return Responce.send(500, {}, "Database connection error")

    cursor = get_cursor()
    if cursor is None:
        return Responce.send(500, {}, "Cursor creation error")

    id = id.split('.')
    if len(id) == 2 and id[1] == 'pdf':
        fullpath = os.path.join(pdfpath, f"{id[0]}.pdf")
        if os.path.exists(fullpath):
            try:
                cursor.execute(f"SELECT * FROM pdfs WHERE id='{id[0]}';")
                row = cursor.fetchone()
                return send_file(fullpath, as_attachment=True, download_name=f"{row[1]}-EduVerse.pdf")
            except Exception as e:
                print(f"Error: {e}")
                return Responce.send(500, {}, "Server error")
        return Responce.send(404, {}, "File not found")
    return Responce.send(401, {}, "Invalid file type")

if __name__ == "__main__":
    app.run()
