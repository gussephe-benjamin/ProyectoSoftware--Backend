import json
import boto3
from boto3.dynamodb.conditions import Key
import decimal

dynamodb = boto3.resource('dynamodb')
curso_table = dynamodb.Table('Curso')

# Esta clase se encarga de convertir objetos Decimal en int o float al serializar a JSON
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
        # Extraemos parámetro profesorId de query string
        query_params = event.get('queryStringParameters', {}) or {}
        profesorId = query_params.get('profesorId')

        if not profesorId:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Se debe proporcionar profesorId como parámetro de consulta'
                })
            }

        # Hacemos la consulta al índice secundario 'profesor_index'
        response = curso_table.query(
            IndexName='profesor_index',
            KeyConditionExpression=Key('profesorId').eq(profesorId)
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
                'message': 'Error al obtener cursos del profesor',
                'error': str(e)
            })
        }
