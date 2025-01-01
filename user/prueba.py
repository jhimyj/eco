import json
import os

def lambda_handler(event, context):
    # Imprimir el ARN del pool Cognito desde las variables de entorno
    cognito_pool_arn = os.environ.get("COGNITO_USER_POOL_ARN")
    print("Cognito User Pool ARN:", cognito_pool_arn)

    # Imprimir el evento para ver la estructura
    print("Evento recibido:", json.dumps(event))

    # Extrae la información del usuario autenticado
    user_info = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    
    # Retorna la información del usuario autenticado
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Autenticación exitosa",
            "user_info": user_info
        })
    }
