import json
import boto3
import uuid
import logging
import os
from decimal import Decimal  
from websocket_utils.notify_clients import notify_clients


logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
PLACES_TABLE = os.environ['PLACES_TABLE']

table = dynamodb.Table(PLACES_TABLE)

def create_response(status_code, body):
    """Función para crear una respuesta estándar en el formato adecuado."""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(body)
    }

def lambda_handler(event, context):
    """Manejador de la función Lambda para registrar un lugar."""
    try:
        body = json.loads(event["body"])
        place_id = str(uuid.uuid4()) 
        
        try:
            latitude = Decimal(str(body.get('latitude')))  
            longitude = Decimal(str(body.get('longitude')))  
        except (ValueError, TypeError):
            logger.warning('Latitud y longitud deben ser valores numéricos válidos')
            return create_response(400, {'message': 'Latitud y longitud deben ser valores numéricos válidos'})
        
        pollution_level = body.get('pollution_level')
        plastic_level = body.get("plastic_level")
        status = body.get('status')

    
        missing_fields = []
        for field in ["latitude", "longitude", "pollution_level", "plastic_level", "status"]:
            if not body.get(field):
                missing_fields.append(field)

        if missing_fields:
            logger.warning(f'Campos requeridos faltantes: {", ".join(missing_fields)}')
            return create_response(400, {'message': f'Campos requeridos faltantes: {", ".join(missing_fields)}'})



        table.put_item(
            Item={
                'place_id': place_id,
                'latitude': latitude,
                'longitude': longitude,
                'pollution_level': pollution_level,
                'plastic_level': plastic_level,
                'status': status
            }
        )
        body['place_id'] = place_id
        logger.info(f'Lugar registrado con place_id: {place_id}, latitud: {latitude}, longitud: {longitude}')
        notify_clients(json.dumps({'action':"added",'place':{
        'place_id': place_id,
        'latitude': float(latitude),
        'longitude': float(longitude),
        'pollution_level': pollution_level,
        'plastic_level': plastic_level,
        'status': status
        }}))
        return create_response(201, {'message': 'Lugar registrado correctamente', 'place_id': place_id})
    
    except Exception as e:
        logger.error(f'Error interno del servidor: {str(e)}')
       
        return create_response(500, {'message': str(e)})
