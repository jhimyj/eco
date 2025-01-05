import boto3
import logging
import os
import json
from utils.api_response import Response
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ['USERS_TABLE']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

modifiable_data = ["phone_number", "district"]

def lambda_handler(event, context):
    """
    Función Lambda que maneja la actualización parcial (PATCH) de los datos de un usuario en DynamoDB.
    
    Args:
        event (dict): El evento de la solicitud que contiene los datos del usuario a actualizar.
        context (object): El contexto de ejecución de la función Lambda.

    Returns:
        dict: La respuesta de la API con el resultado de la operación.
    """
    try:
        logger.info("Inicio de la función lambda_handler.")

        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        logger.info(f"Cuerpo de la solicitud recibido: {body}")

        update_data = {}

        for field in modifiable_data:
            if field in body:  
                update_data[field] = body[field]

        if not update_data:
            logger.warning("No se proporcionaron datos válidos para actualizar.")
            return Response(
                status_code=400,
                message="No se ha proporcionado ningún dato válido para actualizar"
            ).to_dict()

        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            logger.error("No se pudo obtener el ID de usuario de Cognito.")
            return Response(
                status_code=400,
                message="No se pudo obtener el ID de usuario de Cognito."
            ).to_dict()

        logger.info(f"ID de usuario obtenido de Cognito: {user_id}")

        update_data['updated_at'] = datetime.utcnow().isoformat()

        update_expression = "SET " + ", ".join([f"#{key} = :{key}" for key in update_data.keys()])
        expression_attribute_values = {f":{key}": value for key, value in update_data.items()}
        expression_attribute_names = {f"#{key}": key for key in update_data.keys()}

        update_params = {
            'Key': {'user_id': user_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_attribute_values,
            'ExpressionAttributeNames': expression_attribute_names,
            'ReturnValues': 'UPDATED_NEW'
        }

        logger.info(f"Parámetros de actualización preparados: {update_params}")

        response = dynamodb.Table(USERS_TABLE).update_item(**update_params)

        if 'Attributes' not in response:
            logger.error(f"El usuario con ID {user_id} no existe en la base de datos.")
            return Response(
                status_code=404,
                message="El usuario que intentas actualizar no existe. Por favor, termina de configurar tu perfil."
            ).to_dict()

        logger.info(f"Datos actualizados para el usuario {user_id}: {response}")

        return Response(
            status_code=200,
            message="Datos actualizados correctamente",
            body=response['Attributes']
        ).to_dict()

    except Exception as e:
        logger.error(f"Error procesando la solicitud: {e}", exc_info=True)
        return Response(
            status_code=500,
            message="Error interno del servidor"
        ).to_dict()
