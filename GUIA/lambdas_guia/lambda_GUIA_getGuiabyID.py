import json
import boto3
from botocore.exceptions import ClientError
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
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))
        guia_id = int(path_params.get('guia_id'))

        # Obtener la guía por guia_id (clave primaria)
        response = tabla_guias.get_item(Key={'guia_id': guia_id})
        guia = response.get('Item')

        if not guia:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': f'Guía {guia_id} no encontrada'})
            }

        # Validar que la guía pertenezca al curso indicado
        if guia.get('curso_id') != curso_id:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'message': f'La guía {guia_id} no pertenece al curso {curso_id}'})
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'guia': convertir_decimales(guia)})
        }

    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error en DynamoDB',
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
