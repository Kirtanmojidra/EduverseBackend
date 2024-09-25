from flask import request
from ..JWT import JWT
from ..Responcehandler import Responce

def process(cur):
    if not request.args.get("subject") or not request.args.get("sem"):
        return Responce.send(401, {}, "parameter missing")
    subject = request.args.get("subject")
    sem = request.args.get("sem")
    userid = ''
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
            SELECT username, title, sub, sem, id, upload_date
            FROM pdfs
            INNER JOIN users ON pdfs.userid=users.userid
            WHERE pdfs.sem=%s AND pdfs.sub=%s
        """, (sem, subject))
        rows = cur.fetchall()

        if not rows:
            return Responce.send(401, {}, "PDF not found with this data")
        cur.execute("SELECT pdf_id FROM bookmarks WHERE userid=%s", (userid,))
        bookmarks = {row[0] for row in cur.fetchall()}

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
