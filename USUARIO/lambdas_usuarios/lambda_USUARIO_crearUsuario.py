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
        body = json.loads(event['body'])
        uid = body['uid']
        email = body['email']
        role = body['role']
        nombre = body.get('nombre', email.split('@')[0])

        # 1. Verificar si el usuario ya existe
        response = tabla_usuarios.get_item(Key={'uid': uid})
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Usuario ya registrado',
                    'usuario': response['Item']
                })
            }

        # 2. Guardar el nuevo usuario
        nuevo_usuario = {
            'uid': uid,
            'email': email,
            'role': role,
            'nombre': nombre
        }

        tabla_usuarios.put_item(Item=nuevo_usuario)

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Usuario creado correctamente',
                'usuario': nuevo_usuario
            })
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
                'message': 'Error interno al procesar usuario',
                'error': str(e)
            })
        }