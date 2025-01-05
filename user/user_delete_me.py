import boto3
import logging
import os
from utils.api_response import Response


cognito_client = boto3.client('cognito-idp')
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')

USER_POOL_ID = os.environ.get('USER_POOL_ID')
DYNAMODB_TABLE_NAME = os.environ.get('USERS_TABLE')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda para eliminar un usuario en este orden:
    1. Cognito
    2. DynamoDB
    3. S3
    """
    try:
        
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            logger.warning("No se pudo obtener el ID de usuario.")
            return Response(
                status_code=400,
                message="Se requiere el ID del usuario para realizar la eliminación."
            ).to_dict()

        
        try:
            cognito_client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=user_id)
            logger.info(f"Usuario {user_id} eliminado de Cognito.")
        except Exception as e:
            logger.error(f"Error al eliminar usuario {user_id} de Cognito: {e}")
            return Response(
                status_code=500,
                message="Error al eliminar el usuario de Cognito."
            ).to_dict()

        try:
            table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
            response = table.get_item(Key={"user_id": user_id})

            if "Item" in response:
                table.delete_item(Key={"user_id": user_id})
                logger.info(f"Usuario {user_id} eliminado de DynamoDB.")
            else:
                logger.info(f"Usuario {user_id} no encontrado en DynamoDB.")
        except Exception as e:
            logger.error(f"Error al eliminar usuario {user_id} de DynamoDB: {e}")

       
        try:
            file_name = f"profile_pictures/{user_id}.jpeg"
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_name)
            logger.info(f"Imagen {file_name} eliminada de S3.")
        except Exception as e:
            logger.warning(f"Error al eliminar imagen {file_name} de S3: {e}")

        return Response(
            status_code=200,
            message="Usuario eliminado correctamente de Cognito, DynamoDB y S3."
        ).to_dict()

    except Exception as e:
        logger.error(f"Error inesperado al eliminar el usuario: {e}", exc_info=True)
        return Response(
            status_code=500,
            message="Error interno del servidor."
        ).to_dict()
