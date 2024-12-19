import boto3
import json
import os
import logging

s3_client = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        bucket_name = os.getenv('S3_BUCKET')  

        if not bucket_name:
            logger.error("El nombre del bucket no está configurado.")
            return create_response(500, json.dumps({'message': 'El nombre del bucket no está configurado.'}))
        
        place_id = event.get('queryStringParameters', {}).get('place_id', '')
        
        if not place_id:
            logger.warning("No se ha proporcionado un place_id.")
            return create_response(400, json.dumps({'message': 'Se debe proporcionar un place_id en los parámetros de consulta.'}))

        logger.info(f"Recibiendo solicitud para listar archivos en el bucket '{bucket_name}' con el place_id '{place_id}'.")
        
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=place_id)
        
        if 'Contents' not in response:
            logger.info(f"No se encontraron archivos en el prefijo '{place_id}'.")
            return create_response(404, json.dumps({'message': 'No se encontraron archivos para el place_id especificado.'}))
        
        urls = []
        for obj in response['Contents']:
            file_name = obj['Key']
            url = s3_client.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name, 'Key': file_name},
                                                  ExpiresIn=3600)  
            urls.append(url)
        
        logger.info(f"Se generaron {len(urls)} URLs firmadas para los archivos en '{place_id}'.")
        
        return create_response(200, json.dumps({'message': 'URLs generadas correctamente', 'urls': urls}))

    except Exception as e:
        logger.error(f"Error al procesar la solicitud: {str(e)}")
        return create_response(500, json.dumps({'message': 'Error interno del servidor. Por favor, intente más tarde.'}))
