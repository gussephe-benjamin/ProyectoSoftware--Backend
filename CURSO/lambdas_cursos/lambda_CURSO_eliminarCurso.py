import json
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
cursos_table = dynamodb.Table('Curso')
guias_table = dynamodb.Table('Guia')
evaluaciones_table = dynamodb.Table('Evaluacion')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    headers = {'Content-Type': 'application/json'}

    try:
        curso_id = int(event['pathParameters']['id'])

        # 1. Verificar si el curso existe
        curso = cursos_table.get_item(Key={'curso_id': curso_id}).get('Item')
        if not curso:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Curso no encontrado'})
            }

        # 2. Consultar todas las guías del curso
        guias_response = guias_table.query(
            IndexName='curso_index',
            KeyConditionExpression=Key('curso_id').eq(curso_id)
        )
        guias = guias_response.get('Items', [])

        # 3. Eliminar evaluaciones asociadas a cada guía
        for guia in guias:
            evaluacion_ids = guia.get('evaluacionIds', [])
            for eid in evaluacion_ids:
                eid_val = int(eid) if isinstance(eid, (str, int, Decimal)) else int(eid.get('N'))
                evaluaciones_table.delete_item(Key={'evaluacion_id': eid_val})

            # 4. Eliminar la guía
            guias_table.delete_item(Key={'guia_id': guia['guia_id']})

        # 5. Eliminar el curso
        delete_response = cursos_table.delete_item(
            Key={'curso_id': curso_id},
            ReturnValues='ALL_OLD'
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Curso, guías y evaluaciones eliminadas correctamente',
                'cursoEliminado': delete_response.get('Attributes', {})
            }, default=decimal_default)
        }

    except Exception as e:
        print(f"Error al eliminar curso y relaciones: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error interno al eliminar curso y elementos relacionados',
                'error': str(e)
            })
        }
