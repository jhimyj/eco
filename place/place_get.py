import boto3
import json
import os
import logging
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
PLACES_TABLE = os.environ['PLACES_TABLE']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def create_response(status_code, response):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(response, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    try:
        logger.info(f"Evento recibido: {json.dumps(event)}")
        place_id = event.get('pathParameters', {}).get('place_id')
        if not place_id:
            logger.info("El parámetro 'place_id' no fue proporcionado en la solicitud.")
            return create_response(400, {'error': 'El parámetro place_id es obligatorio.'})

        table = dynamodb.Table(PLACES_TABLE)
        response = table.get_item(Key={'place_id': place_id})
        if 'Item' not in response:
            logger.error(f"No se encontró un lugar con place_id {place_id}.")
            return create_response(404, {'error': f'No se encontró un lugar con place_id {place_id}'})

        place = response['Item']
        return create_response(200, place)
    
    except Exception as e:
        logger.error(f"Error procesando la solicitud: {str(e)}")
        return create_response(500, {'error': 'Error interno del servidor'})
