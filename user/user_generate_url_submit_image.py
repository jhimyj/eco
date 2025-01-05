import boto3
import logging
import os
import json
from utils.api_response import Response
from datetime import datetime
from botocore.exceptions import ClientError  # Importa para manejar errores específicos de boto3

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
EXPIRATION_TIME = 3600  # Tiempo de expiración en segundos (1 hora)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Función Lambda que genera una URL prefirmada para cargar una imagen a S3.

    Args:
        event (dict): Evento de la solicitud HTTP, se espera que contenga el contexto de usuario autenticado.
        context (object): Contexto de ejecución de Lambda.

    Returns:
        dict: Respuesta de la API con la URL prefirmada.
    """
    try:
        
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get('sub')

        if not user_id:
            logger.warning("No se pudo obtener el ID de usuario de Cognito.")
            return Response(
                status_code=400,
                message="Se requiere el id del usuario para generar la URL prefirmada."
            ).to_dict()

        
        file_name = f"profile_pictures/{user_id}.jpeg"

       
        try:
            url = s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': BUCKET_NAME, 'Key': file_name,'ContentType': 'image/jpeg'},
                ExpiresIn=EXPIRATION_TIME
            )
            logger.info(f"URL prefirmada generada para el usuario {user_id}: {url}")

            return Response(
                status_code=200,
                message="URL prefirmada generada correctamente",
                body={"url": url}
            ).to_dict()
        
        except ClientError as e:
            logger.error(f"Error al generar la URL prefirmada: {e}", exc_info=True)
            return Response(
                status_code=500,
                message="Error al generar la URL prefirmada."
            ).to_dict()

    except Exception as e:
        logger.error(f"Error inesperado generando la URL prefirmada: {e}", exc_info=True)
        return Response(
            status_code=500,
            message="Error interno del servidor"
        ).to_dict()
