import boto3
import json
import os
import logging
from utils.jwt_utils import generate_jwt
from utils.password_utils import verify_password

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SECRET_KEY = os.getenv('SECRET_KEY', 'mi_clave_secreta')
dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.getenv('USERS_TABLE')
INDEX_EMAIL_NAME = os.getenv('INDEX_EMAIL_NAME')




def create_response(status_code, response):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': response
    }

def lambda_handler(event, context):
    try:
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return create_response(400, json.dumps({'message': 'Email y password son requeridos'}))
        
        table = dynamodb.Table(USERS_TABLE)
        response = table.query(
            IndexName=INDEX_EMAIL_NAME,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
        )
        
        if not response['Items']:
            logger.info(f"Usuario con email {email} no encontrado")
            return create_response(401, json.dumps({'message': 'Credenciales inválidas'}))

        user = response['Items'][0]  
        stored_password_hash = user.get('password')

        if not verify_password(stored_password_hash, password):
            logger.info(f"Contraseña incorrecta para el usuario {email}")
            return create_response(401, json.dumps({'message': 'Credenciales inválidas'}))

        role = user.get('role', 'USER')

        token = generate_jwt(user['user_id'], email, role)

        logger.info(f"Usuario {email} autenticado con éxito")

        return create_response(200, json.dumps({'message': 'Login exitoso', 'token': token}))

    except Exception as e:
        logger.error(f"Error en el proceso de login: {str(e)}", exc_info=True)
        return create_response(500, json.dumps({'message': f'Error en el proceso de login: {str(e)}'}))
