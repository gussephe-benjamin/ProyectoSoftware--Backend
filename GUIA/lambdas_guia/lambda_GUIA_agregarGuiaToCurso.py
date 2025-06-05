import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
tabla_curso = dynamodb.Table('Curso')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))

        body = json.loads(event.get('body', '{}'))
        guia_ids = body.get('guia_ids', [])

        if not isinstance(guia_ids, list) or not all(isinstance(x, int) for x in guia_ids):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'guia_ids debe ser una lista de números enteros'})
            }

        # Obtener la lista actual de guías del curso
        response = tabla_curso.get_item(Key={'curso_id': curso_id})
        curso = response.get('Item')

        if not curso:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': f'Curso {curso_id} no encontrado'})
            }

        guias_actual = curso.get('guias', [])

        # Agregar solo IDs que no estén ya presentes
        nuevos_guias = [g for g in guia_ids if g not in guias_actual]

        if not nuevos_guias:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'No se agregaron guías nuevas, todos ya existían'})
            }

        # Actualizar la lista guias con los nuevos IDs
        tabla_curso.update_item(
            Key={'curso_id': curso_id},
            UpdateExpression='SET guias = list_append(if_not_exists(guias, :empty), :nuevos)',
            ExpressionAttributeValues={
                ':nuevos': nuevos_guias,
                ':empty': []
            }
        )

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Guías agregadas exitosamente',
                'nuevas_guias': nuevos_guias
            })
        }

    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error en DynamoDB',
                'error': e.response['Error']['Message']
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error interno',
                'error': str(e)
            })
        }
