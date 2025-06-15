import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
usuario_table = dynamodb.Table('t_Usuario')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Verificar si 'pathParameters' existe en el evento

        # Imprimir el evento para debug
        print("Evento recibido: ", json.dumps(event))

        if 'path' not in event:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Error con el path '})
            }

        if 'id' not in event['path']:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Falta el parámetro id en la URL'})
            }

        # Obtener el parámetro 'id' desde 'pathParameters'
        uid = event['path']['id']

        if not uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Debe proporcionar un uid'})
            }

        # Buscar el usuario por su uid en DynamoDB
        response = usuario_table.get_item(Key={'uid': uid})
        usuario = response.get('Item')

        if not usuario:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Usuario no encontrado'})
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': {'usuario': usuario}
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': {
                'message': 'Error al obtener el usuario',
                'error': str(e)
            }
        }