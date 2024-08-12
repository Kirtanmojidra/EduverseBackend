from flask  import request,jsonify
import uuid
import os
import datetime
from ..JWT import JWT
from ..app import connectDB
from ..Responcehandler import Responce
allowed_filenames = ['pdf']
rootdir = os.getcwd()
pdfpath = os.path.join(rootdir, "api", "uploadpdf/")
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
    con, cur = connectDB()
    
    if 'file' not in request.files:
        return Responce.send(400, {}, "No file part in the request")
    
    file = request.files['file']
    if file.filename == '':
        return Responce.send(400, {}, "No selected file")
    
    if not allowed_file(file.filename):
        return Responce.send(400, {}, "Invalid file type")
    
    title = request.form.get('title')
    subject = request.form.get('subject')
    sem = request.form.get('sem')
    if not title or not subject or not sem:
        return Responce.send(400, {}, "Missing required form data: title, subject, or sem")
    if sem == '1':
        if subject not in sem1:
            return Responce.send(400, {}, "Subject is not valid for sem 1")
    if sem == '2':
        if subject not in sem2:
            return Responce.send(400, {}, "Subject is not valid for sem 2")
    if sem == '3':
        if subject not in sem3:
            return Responce.send(400, {}, "Subject is not valid for sem 3")
    if sem == '4':
        if subject not in sem4:
            return Responce.send(400, {}, "Subject is not valid for sem 4")
    if sem == '5':
        if subject not in sem5:
            return Responce.send(400, {}, "Subject is not valid for sem 5")
    if sem ==  '6':
        if subject not in sem6:
            return Responce.send(400, {}, "Subject is not valid for sem 6")
    if sem > '7':
        return Responce.send(400, {}, "Invalid sem number")
    try:
        pdf_id = str(uuid.uuid4())
        filename = pdf_id + ".pdf"
        file_path = os.path.join(pdfpath, filename)
        
        cur.execute("SELECT * FROM pdfs WHERE pdf_path=%s;", (filename,))
        if cur.fetchone():
            return Responce.send(409, {}, "PDF already exists")
        
        file.save(file_path)
        
        cur.execute(
            "INSERT INTO pdfs (id, pdf_path, title, subject, sem, date) VALUES (%s, %s, %s, %s, %s, %s);",
            (pdf_id, filename, title, subject, sem, datetime.now())
        )
        con.commit()
        return Responce.send(200, {}, "File uploaded successfully")
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Server error while uploading file")

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS