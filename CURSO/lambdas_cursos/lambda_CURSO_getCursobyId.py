import json
import boto3
from botocore.exceptions import ClientError
import decimal

dynamodb = boto3.resource('dynamodb')
curso_table = dynamodb.Table('Curso')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Obtener el curso_id desde pathParameters
        path_params = event.get('pathParameters', {})
        curso_id_str = path_params.get('id')

        if not curso_id_str:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'El parámetro curso_id es obligatorio'})
            }

        try:
            curso_id = int(curso_id_str)
        except ValueError:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'curso_id debe ser un número válido'})
            }

        # Buscar el curso por su clave primaria
        response = curso_table.get_item(Key={'curso_id': curso_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': f'No se encontró curso con ID {curso_id}'})
            }

        curso = response['Item']

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'curso': curso}, cls=DecimalEncoder)
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
                'message': 'Error interno al obtener el curso',
                'error': str(e)
            })
        }
