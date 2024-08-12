from flask import request, jsonify
import uuid
import os
from datetime import date
from ..JWT import JWT
from ..Responcehandler import Responce

allowed_filenames = ['pdf']
rootdir = os.getcwd()
pdfpath = os.path.join(rootdir, "api", "uploadpdf/")

semesters = {
    1: ["sem-1-syllabus", "DSC-C-BCA-111T", "DSC-M-BCA-113T", "MDC-BCA-114 T", "SEC-OOS-116", "VAC-117", 
        "DSC-C-BCA-111T-old-paper", "DSC-M-BCA-113T-old-paper", "MDC-BCA-114 T-old-paper", "AEC-ENG-115-old-paper", 
        "SEC-OOS-116-old-paper", "VAC-117-old-paper", "DSC-C-BCA-112P", "DSC-M-BCA-113P", "MDC-BCA-114P"],
    2: ["DSC-C-BCA-121 T", "SEC-BCA-126", "IDC-BCA-124 T", "DSC-M-BCA-123 T", "DSC-M-BCA-123 P", "DSC-C-BCA-122 P",
        "IDC-BCA-124 P", "DSC-C-BCA-121 T-old-paper", "SEC-BCA-126-old-T-old-paper", "IDC-BCA-124 T-old-paper", 
        "DSC-M-BCA-123 T-old-paper"],
    3: [],
    4: [],
    5: ["sem-5-syllabus", "cc-301", "cc-302", "cc-303", "sec-301", "cc-304", "cc-305", 
        "cc-301-old-paper", "cc-302-old-paper", "cc-303-old-paper", "sec-301-c-old-paper"],
    6: ["sem-6-syllabus", "CC-307", "CC-308", "CC-309", "SEC-302 (C)", "cc-310", "cc-311", 
        "CC-307-oldpaper", "CC-308-oldpaper", "CC-309-oldpaper", "SEC-302 (C)-oldpaper"]
}

def UploadPdf(app, cur, con):
    # Authentication
    cookie = request.cookies.get("session")
    if not cookie:
        return Responce.send(401, {}, "Not Authenticated")

    try:
        decoded_cookie = JWT.decode(cookie)
        if not decoded_cookie:
            return Responce.send(401, {}, "Not Authenticated")
    except Exception as e:
        print(e)
        return Responce.send(401, {}, "Not Authenticated")

    # Validate file
    if 'pdf' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    if file_ext not in allowed_filenames:
        return Responce.send(402, {}, "Invalid file type")

    # Validate form data
    title = request.form.get("title")
    subject = request.form.get("subject")
    semester = request.form.get("sem")
    user_id = decoded_cookie.get("data")

    if not all([title, subject, semester, user_id]):
        return Responce.send(400, {}, "Missing required parameters")

    try:
        semester = int(semester)
        if semester not in semesters or subject not in semesters[semester]:
            return Responce.send(402, {}, "Invalid subject for the given semester")
    except ValueError as e:
        print(e)
        return Responce.send(402, {}, "Invalid semester format")

    # Save file and update database
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.pdf"
    try:
        file.save(os.path.join(pdfpath, filename))
        datetoday = date.today().isoformat()
        cur.execute(f"insert into pdfs values('{file_id}','{title}','{subject}','{semester}','{user_id}','{datetoday}','{filename}');")
        con.commit()
        return Responce.send(200, {}, "File uploaded successfully")
    except Exception as e:
        print(e)
        return Responce.send(500, {}, "Error while uploading file")
