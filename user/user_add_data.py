import boto3
import json
import os
import logging
from utils.api_response import Response

dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ['USERS_TABLE']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

required_data = ["phone_number", "district"]


def lambda_handler(event, context):
    """
    Función Lambda que valida los datos y guarda el usuario en DynamoDB.

    Args:
        event (dict): El evento de la solicitud.
        context (object): El contexto de ejecución de la función Lambda.

    Returns:
        dict: La respuesta de la API con el resultado de la operación.
    """
    try:
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)

        item = {}
        missing_fields = []

        for field in required_data:
            value = body.get(field)
            if not value:
                missing_fields.append(field)
            else:
                item[field] = value
        
        if missing_fields:
            logger.warning(f"Campos requeridos faltantes: {', '.join(missing_fields)}")
            return Response(status_code=400, message="Campos requeridos faltantes", body={"Campos requeridos faltantes": missing_fields}).to_dict()
        

        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get('sub')
        if not user_id:
            logger.warning("No se pudo obtener el ID de usuario de Cognito.")
            return Response(status_code=400,message="No se pudo obtener el ID de usuario de Cognito.").to_dict()
        

        table = dynamodb.Table(USERS_TABLE)
        item['user_id'] = user_id
        item['created_at'] = context.aws_request_id

        table.put_item(Item=item)

        logger.info(f"Usuario {user_id} guardado correctamente: {item}")
        return Response(status_code=201,message="Datos guardados correctamente",body={'user':item}).to_dict()

    except Exception as e:
        logger.error(f"Error procesando la solicitud: {e}", exc_info=True)
        return Response(status_code=500, message="Error interno del servidor").to_dict()
