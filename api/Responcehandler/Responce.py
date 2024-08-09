from flask import make_response,jsonify
def send(code,data,message):
    try:
        res = {
            "status_code":code,
            "data":data,
            "message":message,
            }
    except:
        return make_response({"message":"error while prsing data"},500)
    try:
        res = make_response(jsonify(res),code)
        return res
    except Exception as e:
        print(e)
        return False
    