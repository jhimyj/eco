import json

def lambda_handler(event, context):
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
