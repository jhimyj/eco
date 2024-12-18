from datetime import datetime, timedelta
import jwt 
import os


class TokenExpiredError(Exception):
    pass
class InvalidTokenError(Exception):
    pass


SECRET_KEY = os.getenv('SECRET_KEY', 'mi_clave_secreta')

def generate_jwt(user_id, email, role):
    expiration_time = datetime.utcnow() + timedelta(hours=6)
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': expiration_time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token



def decode_jwt(token):
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("El token ha expirado.")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Token no válido.")