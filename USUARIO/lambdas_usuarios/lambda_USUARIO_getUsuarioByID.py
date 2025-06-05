import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
usuario_table = dynamodb.Table('Usuario')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Obtener uid desde los parámetros de ruta
        uid = event['pathParameters'].get('user_id')

        if not uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Debe proporcionar un uid'})
            }

        # Buscar usuario por su uid (PK)
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
            'body': json.dumps({'usuario': usuario})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al obtener el usuario',
                'error': str(e)
            })
        }