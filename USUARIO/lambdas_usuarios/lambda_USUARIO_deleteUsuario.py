import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
tabla_usuarios = dynamodb.Table('Usuario')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:

        # Obtener uid desde el path
        uid = event['pathParameters'].get('user_id')

        if not uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'El parámetro uid es obligatorio en el path'})
            }

        # Verificar si existe
        response = tabla_usuarios.get_item(Key={'uid': uid})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Usuario no encontrado'})
            }

        # Eliminar el usuario
        tabla_usuarios.delete_item(Key={'uid': uid})

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': f'Usuario {uid} eliminado correctamente'})
        }

    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al acceder a DynamoDB',
                'error': str(e)
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error interno al eliminar usuario',
                'error': str(e)
            })
        }
