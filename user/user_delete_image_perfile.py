import boto3
import logging
import os
from utils.api_response import Response
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Función Lambda que elimina una imagen de perfil en S3.

    Args:
        event (dict): Evento de la solicitud HTTP, se espera que contenga el contexto de usuario autenticado.
        context (object): Contexto de ejecución de Lambda.

    Returns:
        dict: Respuesta de la API con el resultado de la operación.
    """
    try:
       
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get('sub')

        if not user_id:
            logger.warning("No se pudo obtener el ID de usuario de Cognito.")
            return Response(
                status_code=400,
                message="Se requiere el id del usuario para eliminar la imagen."
            ).to_dict()

        
        file_name = f"profile_pictures/{user_id}.jpeg"

        
        try:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_name)
            logger.info(f"Imagen eliminada exitosamente para el usuario {user_id}: {file_name}")

            return Response(
                status_code=200,
                message="Imagen eliminada exitosamente."
            ).to_dict()

        except ClientError as e:
            logger.error(f"Error al intentar eliminar la imagen {file_name}: {e}", exc_info=True)
            return Response(
                status_code=500,
                message="Error al intentar eliminar la imagen."
            ).to_dict()

    except Exception as e:
        logger.error(f"Error inesperado al eliminar la imagen: {e}", exc_info=True)
        return Response(
            status_code=500,
            message="Error interno del servidor"
        ).to_dict()
