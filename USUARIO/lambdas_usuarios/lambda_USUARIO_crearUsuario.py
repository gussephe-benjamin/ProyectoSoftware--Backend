import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
tabla_usuarios = dynamodb.Table('t_Usuario')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        body = event['body']

    except json.JSONDecodeError as json_err:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': {
                'message': 'Error al procesar el cuerpo de la solicitud',
                'error': 'JSON inválido'
            }
    }

    try:
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
                'body': {
                    'message': 'Usuario ya registrado',
                    'usuario': response['Item']
                }
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
            'body': {
                'message': 'Usuario creado correctamente',
                'usuario': nuevo_usuario
            }
        }

    except ClientError as e:
        error_message = str(e) 
        return {
            'statusCode': 500,
            'headers': headers,
            'body': {
                'message': 'Error al acceder a DynamoDB',
                'error': error_message
            }
        }

    except Exception as e:
        error_message = str(e) 
        return {
            'statusCode': 500,
            'headers': headers,
            'body': {
                'message': 'Error interno al procesar usuario',
                'error': error_message
            }
        }