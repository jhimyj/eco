from datetime import datetime, timedelta
import jwt 
import os

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

