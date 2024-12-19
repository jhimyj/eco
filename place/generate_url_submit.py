import boto3
import os
import json
import uuid
import datetime
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3_client = boto3.client('s3')
bucket_name = os.environ['S3_BUCKET']

def create_response(status_code, response):
    """
    Crea una respuesta estándar para Lambda.
    
    Args:
        status_code (int): Código de estado HTTP.
        response (dict): El cuerpo de la respuesta en formato JSON.
    
    Returns:
        dict: Un diccionario con el código de estado, encabezados y el cuerpo de la respuesta.
    """
    logger.info(f"Creando respuesta con status code {status_code} y respuesta: {response}")
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(response)
    }

def lambda_handler(event, context):
    """
    Controlador principal para generar URLs firmadas para subir archivos a S3.
    
    Esta función recibe una lista de archivos, genera un nombre único para el
    directorio en S3 y proporciona una URL firmada para cada archivo, lo que 
    permite a un cliente subir los archivos a un bucket de S3 de forma segura.

    Args:
        event (dict): El evento que invoca la función Lambda, que contiene los detalles de los archivos a subir.
        context (object): El contexto de ejecución de Lambda, no utilizado en este caso.
    
    Returns:
        dict: Respuesta en formato JSON que incluye las URLs firmadas para subir los archivos.
    """
    try:
        logger.info("Iniciando la función Lambda para generar URLs firmadas")
        

        body = event.get("body", {})

        if not body:
            logger.warning("El cuerpo de la solicitud está vacío")
            return create_response(400, {'message': 'Cuerpo de la solicitud vacío'})
        
        if isinstance(body, str):
            body = json.loads(body)

        files = body.get('files', [])
        if not files:
            logger.warning("No se proporcionaron archivos")
            return create_response(400, {'message': 'Se requiere al menos un archivo'})

        directory = body.get('directory', '')
        if not directory:
            logger.warning("No se proporcionó el directorio")
            return create_response(400, {'message': 'El campo "directory" es requerido'})

        
        urls = []

        logger.info(f"Generando directorio único: {directory}")

        for file in files:
            original_file_name = file.get('file_name')
            if not original_file_name:
                logger.warning("Archivo sin nombre")
                return create_response(400, {'message': 'Cada archivo debe tener un nombre'})

            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8]  
            unique_file_name = f"{timestamp}-{unique_id}-{original_file_name}"
            
            file_name = f"{directory}/{unique_file_name}"
            content_type = file.get('content_type', 'application/octet-stream')

            logger.info(f"Generando URL firmada para el archivo: {file_name}")
            
            
            try:
                presigned_url = s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': file_name,
                        'ContentType': content_type,
                    },
                    ExpiresIn=3600
                )
            except Exception as e:
                logger.error(f"Error al generar la URL firmada para el archivo {file_name}: {str(e)}")
                return create_response(500, {'message': f'Error al generar la URL para el archivo {file_name}'})

            urls.append({'file_name': file_name, 'url': presigned_url})

        logger.info(f"URLs firmadas generadas exitosamente: {urls}")

        return create_response(200, {
            'urls': urls
        })

    except Exception as e:
        logger.error(f"Error al procesar la solicitud: {str(e)}")
        return create_response(500, {'message': 'Ocurrió un error interno. Por favor intente de nuevo más tarde.'})
