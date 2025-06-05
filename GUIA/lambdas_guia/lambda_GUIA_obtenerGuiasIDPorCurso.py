import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tabla_cursos = dynamodb.Table('Curso')
tabla_guias = dynamodb.Table('Guia')

# Función para convertir Decimals a int o float
def convertir_decimales(obj):
    if isinstance(obj, list):
        return [convertir_decimales(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convertir_decimales(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
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
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))

        response = tabla_cursos.get_item(Key={'curso_id': curso_id})
        curso = response.get('Item')

        if not curso:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': f'Curso {curso_id} no encontrado'})
            }

        guia_ids = curso.get('guias', [])

        if not guia_ids:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'guias': []})
            }

        keys = [{'guia_id': gid} for gid in guia_ids]

        batch_response = dynamodb.batch_get_item(
            RequestItems={
                'Guia': {
                    'Keys': keys
                }
            }
        )

        guias_encontradas = batch_response['Responses'].get('Guia', [])
        guias_convertidas = convertir_decimales(guias_encontradas)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'guias': guias_convertidas})
        }

    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al acceder a DynamoDB',
                'error': e.response['Error']['Message']
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error interno',
                'error': str(e)
            })
        }
