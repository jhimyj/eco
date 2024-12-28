import json
import boto3
import logging
import os
from decimal import Decimal
from websocket_utils.notify_clients import notify_clients
from botocore.exceptions import ClientError

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
        updatable_fields = ["plastic_level", "pollution_level", "latitude", "longitude", "status"]
        update_expression = 'set '
        expression_attribute_values = {}
        body = json.loads(event.get("body", "{}"))
        place_id = event.get('pathParameters', {}).get('place_id')

        if not place_id:
            logger.error("El parámetro 'place_id' no fue proporcionado en la solicitud.")
            return create_response(400, {'message': 'El parámetro place_id es obligatorio.'})

        if not body:
            logger.error("'body' está vacío o mal formado.")
            return create_response(400, {'message': 'El cuerpo de la solicitud está vacío o mal formado.'})

        updated_fields_found = False
        for field in updatable_fields:
            if field in body:
                value = body[field]
                if isinstance(value, (int, float)):
                    value = Decimal(str(value))
                if updated_fields_found:
                    update_expression += ', '
                update_expression += f"{field} = :{field}"
                expression_attribute_values[f":{field}"] = value
                updated_fields_found = True

        if not updated_fields_found:
            logger.error("No hay datos válidos para actualizar.")
            return create_response(400, {'message': 'No se encontraron claves válidas para actualizar en el cuerpo de la solicitud.'})

        logger.info(f"Intentando actualizar el lugar con ID: {place_id}")

        condition_expression = "attribute_exists(place_id)"

        response = table.update_item(
            Key={'place_id': place_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression=condition_expression,
            ReturnValues="ALL_NEW"
        )

        if 'Attributes' in response:
            updated_item = json.dumps(response['Attributes'], cls=DecimalEncoder)
            logger.info(f"Lugar actualizado: {updated_item}")
            
            notify_clients(json.dumps({'action': 'updated', 'place': json.loads(updated_item)}))

        return create_response(200, {'message': 'Lugar actualizado correctamente.', 'data': response['Attributes']})

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ConditionalCheckFailedException':
            logger.error(f"No se encontró el lugar con ID: {place_id}")
            return create_response(404, {'message': f'place_id {place_id} no encontrado.'})
        else:
            logger.error(f"Error al interactuar con DynamoDB: {str(e)}")
            return create_response(500, {'message': 'Error interno en DynamoDB.'})

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return create_response(500, {'message': 'Error inesperado del servidor.'})
