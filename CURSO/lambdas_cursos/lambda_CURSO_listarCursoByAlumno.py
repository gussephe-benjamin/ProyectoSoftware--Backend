import json
import boto3
from boto3.dynamodb.conditions import Attr
import decimal

dynamodb = boto3.resource('dynamodb')
curso_table = dynamodb.Table('Curso')

# Convierte objetos Decimal a valores nativos para JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    headers = {'Content-Type': 'application/json'}

    try:
        # Extraemos parámetro estudiante_uid de query string
        query_params = event.get('queryStringParameters', {}) or {}
        estudiante_uid = query_params.get('estudiante_uid')

        if not estudiante_uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Se debe proporcionar estudiante_uid como parámetro de consulta'
                })
            }

        # Hacemos un scan filtrando por la lista 'estudiantes' que contenga al UID dado
        response = curso_table.scan(
            FilterExpression=Attr('estudiantes').contains(estudiante_uid)
        )
        cursos = response.get('Items', [])

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'cursos': cursos}, cls=DecimalEncoder)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al obtener cursos del estudiante',
                'error': str(e)
            })
        }
