import boto3
import logging
import json
import os
import uuid
from utils.password_utils import hash_password

logger = logging.getLogger()
logger.setLevel(logging.INFO)


##############
dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ['USERS_TABLE']
INDEX_EMAIL_NAME = os.environ['INDEX_EMAIL_NAME']



def create_response(status_code, response):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': response
    }

def email_exists(email):
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.query(
            IndexName=INDEX_EMAIL_NAME,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
        )
        return response['Count'] > 0
    except Exception as e:
        logger.error(f"Error verificando existencia del email: {e}", exc_info=True)
        raise


def lambda_handler(event, context):
    try:
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)

        data = body.get("data")
        email = body.get("email")
        password = body.get("password")

        missing_fields = []
        for field in ["data","name", "last_name", "phone", "district", "email", "password"]:
            if not body.get(field) and not data.get(field):
                missing_fields.append(field)

        if missing_fields:
            logger.warning(f"Faltan campos requeridos: {missing_fields}")
            response = json.dumps({"message": f"Campos requeridos faltantes: {', '.join(missing_fields)}"})
            return create_response(400, response)
        
        if email_exists(email):
            logger.info(f"El email {email} ya existe en la base de datos.")
            return create_response(400, json.dumps({"message": "El email ya está registrado."}))
        
        hashed_password = hash_password(password)

        user_id = str(uuid.uuid4())



        item = {
            'user_id': user_id,
            "email": email,
            "data": data,
            "password": hashed_password,
            "role": "USER",
            "created_at": context.aws_request_id
        }

        table = dynamodb.Table(USERS_TABLE)
        table.put_item(Item=item)

        logger.info(f"Datos guardados: {item}")
        return create_response(201, json.dumps({"message": "Datos guardados correctamente"}))

    except Exception as e:
        logger.error(f"Error procesando la solicitud: {e}", exc_info=True)
        return create_response(500, json.dumps({"message": "Error interno del servidor"}))
