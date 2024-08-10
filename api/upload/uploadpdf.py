from flask  import request,jsonify
import uuid
import os
from datetime import date
from ..JWT import JWT
from ..Responcehandler import Responce
allowed_filenames = ['pdf']
rootdir = os.getcwd()
pdfpath = rootdir + "/api/uploadpdf/"
sem1=["sem-1-syllabus",
    "DSC-C-BCA-111T",
    "DSC-M-BCA-113T",
    "MDC-BCA-114 T",
    "SEC-OOS-116",
    "SEC-OOS-116",
    "VAC-117",
    "DSC-C-BCA-111T-old-paper",
    "DSC-M-BCA-113T-old-paper",
    "MDC-BCA-114 T-old-paper",
    "AEC-ENG-115-old-paper",
    "SEC-OOS-116-old-paper",
    "VAC-117-old-paper",
    "DSC-C-BCA-112P",
    "DSC-M-BCA-113P",
    "MDC-BCA-114P"]
sem2=[  "DSC-C-BCA-121 T",
    "SEC-BCA-126",
    "IDC-BCA-124 T",
    "DSC-M-BCA-123 T",
    "DSC-M-BCA-123 P",
    "DSC-C-BCA-122 P",
    "IDC-BCA-124 P",
    "DSC-C-BCA-121 T-old-paper",
    "SEC-BCA-126-old-T-old-paper",
    "IDC-BCA-124 T-old-paper",
    "DSC-M-BCA-123 T-old-paper"]
sem3=[""]
sem4=[""]
sem5=["sem-5-syllabus"
    "cc-301",
    "cc-302",
    "cc-303",
    "sec-301",
    "cc-304",
    "cc-305",
    "cc-301-old-paper",
    "cc-302-old-paper",
    "cc-303-old-paper",
    "sec-301-c-old-paper"]
sem6=[ "sem-6-syllabus",
    "CC-307",
    "CC-308",
    "CC-309",
    "SEC-302 (C)",
    "cc-310",
    "cc-311",
    "CC-307-oldpaper",
    "CC-308-oldpaper",
    "CC-309-oldpaper",
    "SEC-302 (C)-oldpaper"]
def UploadPdf(app,cur,con):
    try:
        cookie = request.cookies.get("session")
        if cookie:
            decoded_cookie = JWT.decode(cookie)
            if decoded_cookie:
                pass
        else:
            return Responce(401,{},"Not Authenticated--")
    except:
        return Responce.send(401,{},"not authenticated ---")
    userObject={}
    if 'pdf' not in request.files:
        return jsonify({'message': 'Not selected pdf'}), 400

    file = request.files['pdf']
    file_ext = file.filename.split('.')
    file_ext = file_ext[-1]
    if file.filename == '':
        return jsonify({'message': 'Not selected pdf'}), 400
    if file_ext not in allowed_filenames:
        return Responce.send(402,{},"file type is not valid")
    fileid = uuid.uuid4()
    filename = f"{fileid}.pdf"
    try:
        userObject["title"] = request.form.get("title")
        userObject["sub"] = request.form.get("subject")
        userObject["sem"] = request.form.get("sem")
        userObject["userid"] = decoded_cookie["data"]

        if(userObject["title"] is not None
           and userObject["sub"] is not None
           and userObject["sem"] is not None
           and userObject["userid"] is not None):
            try:
                if userObject["sem"]== 1:
                    if userObject["sub"] in sem1:
                        pass
                    else:
                        return Responce.send(402,{},"subject is not valid")
                elif userObject["sem"]== 2:
                    if userObject["sub"] in sem2:
                        pass
                    else:
                        return Responce.send(402,{},"subject is not valid")
                elif userObject["sem"]== 3:
                    if userObject["sub"] in sem3:
                        pass
                    else:
                        return Responce.send(402,{},"subject is not valid")
                elif userObject["sem"]== 4:
                    if userObject["sub"] in sem4:
                        pass
                    else:
                        return Responce.send(402,{},"subject is not valid")
                elif userObject["sem"]== 5:
                    if userObject["sub"] in sem5:
                        pass
                    else:
                        return Responce.send(402,{},"subject is not valid")
                elif userObject["sem"]== 6:
                    if userObject["sub"] in sem6:
                        pass
                    else:
                        return Responce.send(402,{},"subject is not valid")
                elif int(userObject["sem"]) > 6:
                    return Responce.send(402,{},"subject name is not valid")
            except Exception as e:
                print(e)
                return Responce.send(402,{},"sem name is not valid")
            try:
                file.save(pdfpath+filename)
                datetoday = f'{date.today()}'
                cur.execute(f"insert into pdfs values('{fileid}','{userObject['title']}','{userObject['sub']}','{userObject['sem']}','{userObject['userid']}','{datetoday}','{filename}');")
                con.commit()
                
            except Exception as e:
                print(e)
                return Responce.send(500,{},f"Error while uploading file")
            return Responce.send(200,{},"file uploaded")
        else:
            print(userObject)
            return Responce.send(401,{},"parameter missing")
    except:
        print(userObject)
        return Responce.send(401,{},"parameter missing")