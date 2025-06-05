import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
tabla_guias = dynamodb.Table('Guia')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))
        guia_id = int(path_params.get('guia_id'))

        body = json.loads(event.get('body', '{}'))
        nuevos_ids = body.get('evaluacion_ids')

        if not isinstance(nuevos_ids, list) or not all(isinstance(eid, int) for eid in nuevos_ids):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'El cuerpo debe contener una lista de números enteros en "evaluacion_ids"'
                })
            }

        # Obtener la guía actual
        respuesta = tabla_guias.get_item(
            Key={
                'guia_id': guia_id
            }
        )

        if 'Item' not in respuesta:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Guía no encontrada'
                })
            }

        guia = respuesta['Item']
        actuales = guia.get('evaluacionIds', [])

        # Filtrar duplicados
        nuevos_unicos = [eid for eid in nuevos_ids if eid not in actuales]
        actualizada = actuales + nuevos_unicos

        # Actualizar en DynamoDB
        tabla_guias.update_item(
            Key={
                'guia_id': guia_id
            },
            UpdateExpression='SET evaluacionIds = :val',
            ExpressionAttributeValues={
                ':val': actualizada
            }
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Evaluaciones agregadas (sin duplicados)',
                'guia_id': guia_id,
                'evaluacion_ids_agregadas': nuevos_unicos
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
