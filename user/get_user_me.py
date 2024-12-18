import boto3
import logging
import json
import os
from utils.jwt_utils import decode_jwt, TokenExpiredError, InvalidTokenError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.getenv('USERS_TABLE')

def create_response(status_code, response):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(response)
    }

def lambda_handler(event, context):
    token = event['headers'].get('Authorization', '').replace('Bearer ', '')

    if not token:
        return create_response(401, {'message': 'Token no proporcionado'})

    try:
        decoded = decode_jwt(token)
        print(decoded)
        table = dynamodb.Table(USERS_TABLE)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(decoded["user_id"])
        )

        print(response)
        user = response.get("Item")

        if user is None:
            return create_response(404, {'message': 'Usuario no encontrado'})

        del user["password"]

        return create_response(200, user)
    
    except TokenExpiredError:
        return create_response(401, {'message': 'Token expirado'})
    
    except InvalidTokenError:
        return create_response(400, {'message': 'Token no válido'})
    
    except Exception as e:
        logger.error(f"Error al procesar el token: {e}")
        return create_response(500, {'message': 'Error interno del servidor'})
