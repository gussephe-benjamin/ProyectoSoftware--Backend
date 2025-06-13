import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
tabla_guias = dynamodb.Table('Guia')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))

        body = json.loads(event['body'])
        nombre = body.get('nombre')

        # Ahora solo validamos que haya nombre
        if not nombre:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Se requiere el nombre de la guía'
                })
            }

        guia_id = int(datetime.utcnow().timestamp() * 1000)
        fecha_creacion = datetime.utcnow().isoformat() + 'Z'

        nueva_guia = {
            'guia_id': guia_id,
            'curso_id': curso_id,
            'nombre': nombre,
            'evaluacionIds': [],
            'publicado': False,
            'fechaCreacion': fecha_creacion,
            'fecha_liberacion_guia': None
        }

        tabla_guias.put_item(Item=nueva_guia)

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Guía creada exitosamente',
                'guiaId': guia_id
            })
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
                'message': 'Error interno al crear la guía',
                'error': str(e)
            })
        }