
import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb')
tabla_ranking = dynamodb.Table('Ranking')

def decimal_to_float(obj):
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        # Convertir a int si es entero, si no float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Obtener curso_id del path
        path_params = event.get('pathParameters') or {}
        curso_id = path_params.get('curso_id')

        if not curso_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Falta el curso_id en los parámetros del path'})
            }

        # Convertir curso_id a número (asegúrate que sea compatible con DynamoDB)
        curso_id = int(curso_id)

        # Hacer query a la tabla con el curso_id como Partition Key
        response = tabla_ranking.query(
            KeyConditionExpression=Key('curso_id').eq(curso_id)
        )

        items = response.get('Items', [])
        items = decimal_to_float(items)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'ranking': items})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
