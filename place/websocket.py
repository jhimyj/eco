import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
connections_table = os.environ['CONNECTIONS_TABLE']

def connect_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    table = dynamodb.Table(connections_table)
    table.put_item(Item={'connectionId': connection_id})
    return {'statusCode': 200, 'body': 'Connected'}

def disconnect_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    table = dynamodb.Table(connections_table)
    table.delete_item(Key={'connectionId': connection_id})
    return {'statusCode': 200, 'body': 'Disconnected'}

def action_handler(event, context):
    message = event.get('body')
    logger.info(f"Mensaje recibido: {message}")
    return {'statusCode': 200, 'body': 'Action processed'}
