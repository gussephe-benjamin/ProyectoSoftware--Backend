import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
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
    headers = {'Content-Type': 'application/json'}

    try:
        query_params = event.get('queryStringParameters', {}) or {}
        profesorId = query_params.get('profesorId')
        estudiante_uid = query_params.get('estudiante_uid')

        if profesorId:
            # Buscar cursos del profesor por GSI
            response = curso_table.query(
                IndexName='profesor_index',
                KeyConditionExpression=Key('profesorId').eq(profesorId)
            )
            cursos = response.get('Items', [])

        elif estudiante_uid:
            # Scan porque estudiantes está en una lista (no puedes indexar directamente arrays)
            response = curso_table.scan(
                FilterExpression=Attr('estudiantes').contains(estudiante_uid)
            )
            cursos = response.get('Items', [])

        else:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Debe proporcionar profesor_uid o estudiante_uid'})
            }

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
                'message': 'Error al obtener cursos',
                'error': str(e)
            })
        }
