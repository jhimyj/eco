import boto3
import logging
import os
import json
from utils.api_response import Response

dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ['USERS_TABLE']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito_atributes_return = ["cognito:username", "name", "family_name", "email"]


def lambda_handler(event, context):
    """
    Función Lambda que maneja la solicitud de obtener los datos del usuario,
    fusionando la información de Cognito con la información almacenada en DynamoDB,
    y verificando si el perfil está completo o no.
    
    Args:
        event (dict): El evento de la solicitud que contiene los datos del usuario.
        context (object): El contexto de ejecución de la función Lambda.
    
    Returns:
        dict: La respuesta de la API con el resultado de la operación.
    """
    try:
        
        user_info_cognito = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
        user_id = user_info_cognito.get("sub")

        if not user_id:
            return Response(
                status_code=400,
                message="No se pudo obtener el ID de usuario de Cognito."
            ).to_dict()

        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'user_id': user_id})

    
        if 'Item' not in response:
            return Response(
                status_code=400, 
                message="Usuario registrado en Cognito pero el perfil está incompleto. Por favor, complete los datos adicionales.",
                body={
                    "cognito_info": {key: user_info_cognito[key] for key in cognito_atributes_return if key in user_info_cognito},
                    "profile_complete": False
                }
            ).to_dict()

        user_item = response['Item']
        
        user = Response.merge_dict(dict1=user_item,dict2=user_info_cognito,keys_to_merge= cognito_atributes_return)


        return Response(
            status_code=200,
            body=user
        ).to_dict()

    except Exception as e:
        logger.error(f"Error procesando la solicitud: {e}", exc_info=True)
        return Response(
            status_code=500,
            message="Error interno del servidor"
        ).to_dict()
