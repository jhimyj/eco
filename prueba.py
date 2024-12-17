import jwt
encoded_jwt = jwt.encode({"some": "payload","role":"ADMIN","name":"Jhimy Jhoel"}, "secret", algorithm="HS256")
print(encoded_jwt)

decode_jwt = jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
print(decode_jwt)