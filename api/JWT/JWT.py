import jwt
secret_key = "thisismysecretkeywhichissettojwt"
def encode(payload):
    try:
        encoded_jwt = jwt.encode(payload, secret_key, algorithm='HS256')
        return encoded_jwt
    except Exception as e:
        print("Jwt Encoding Error:",e)
        return False
def decode(jwt_cookie):
    try:
        decoded_jwt = jwt.decode(jwt_cookie, secret_key, algorithms=['HS256'])
        return decoded_jwt
    except Exception as e:
        print("JWT decoding Error",e)
        return False