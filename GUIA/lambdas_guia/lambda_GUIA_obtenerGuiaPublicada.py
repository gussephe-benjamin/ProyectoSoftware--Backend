import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tabla_guias = dynamodb.Table('Guia')

def convertir_decimales(obj):
    if isinstance(obj, list):
        return [convertir_decimales(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convertir_decimales(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def lambda_handler(event, context):
    headers = {'Content-Type': 'application/json'}

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))

        # Consultar guías publicadas para el curso
        response = tabla_guias.query(
            IndexName='curso_index',
            KeyConditionExpression=Key('curso_id').eq(curso_id),
            FilterExpression=Attr('publicado').eq(True)
        )

        guias_publicadas = convertir_decimales(response.get('Items', []))

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'curso_id': curso_id,
                'guias_publicadas': guias_publicadas
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
