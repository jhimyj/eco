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

def get_all_places():
    try:
        logger.info("Obteniendo todos los lugares de la tabla.")
        response = dynamodb.Table(PLACES_TABLE).scan()
        items = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            logger.info("Paginando resultados de DynamoDB scan...")
            response = dynamodb.Table(PLACES_TABLE).scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        logger.info(f"Se encontraron {len(items)} lugares en la tabla.")
        return create_response(200, items)
    except Exception as e:
        logger.error(f"Error al obtener todos los lugares: {e}")
        return create_response(500, {'error': 'Ocurrió un error al obtener los lugares.'})

def lambda_handler(event, context):
    return get_all_places()
