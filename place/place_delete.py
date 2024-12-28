import json
import boto3
import logging
import os 
from decimal import Decimal
from websocket_utils.notify_clients import notify_clients

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
PLACES_TABLE = os.environ['PLACES_TABLE']
table = dynamodb.Table(PLACES_TABLE)

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
        'body': json.dumps(response)
    }

def lambda_handler(event, context):
    try:
        logger.info(f"Evento recibido: {json.dumps(event)}")
        
        place_id = event.get('pathParameters', {}).get('place_id')
        
        if not place_id:
            logger.warning("El parámetro 'place_id' no fue proporcionado en la solicitud.")
            return create_response(400, {'error': 'El parámetro place_id es obligatorio.'})
        
        logger.info(f"Intentando eliminar el lugar con ID: {place_id}")
        response = table.delete_item(Key={'place_id': place_id}, ReturnValues='ALL_OLD')


        if 'Attributes' in response:
            attributes = json.dumps(response['Attributes'], cls=DecimalEncoder)
            logger.info(f"Ítem encontrado y eliminado: {attributes}")
            
            logger.info(f"Notificando a los clientes sobre el lugar eliminado con ID: {place_id}")
            notify_clients(json.dumps({'action': 'deleted', 'place': json.loads(attributes)}))

            return create_response(204, {})

        logger.warning(f"No se encontró un lugar con ID: {place_id}")
        return create_response(404, {'error': 'place_id no encontrado.'})

    except boto3.exceptions.Boto3Error as e:
        logger.error(f"Error al interactuar con DynamoDB: {str(e)}")
        return create_response(500, {'error': 'Error interno del servidor en DynamoDB.'})
    
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return create_response(500, {'error': 'Error inesperado del servidor.'})
