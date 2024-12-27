import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
connections_table = os.environ['CONNECTIONS_TABLE']

apigw_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f"https://{os.environ['WEBSOCKET_API_ID']}.execute-api.{os.environ['REGION']}.amazonaws.com/{os.environ['STAGE']}"
)

def notify_clients(message):
    table = dynamodb.Table(connections_table)
    connections = table.scan().get('Items', [])

    for connection in connections:
        try:
            apigw_management_client.post_to_connection(
                ConnectionId=connection['connectionId'],
                Data=message
            )
            #agregar loger info
        except Exception as e:
            logger.error(f"Error enviando mensaje a la conexión {connection['connectionId']}: {e}")
