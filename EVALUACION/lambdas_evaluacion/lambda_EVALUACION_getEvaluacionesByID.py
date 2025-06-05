import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tabla_evaluaciones = dynamodb.Table('Evaluacion')

def convertir_decimales(obj):
    if isinstance(obj, list):
        return [convertir_decimales(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convertir_decimales(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))
        guia_id = int(path_params.get('guia_id'))
        evaluacion_id = int(path_params.get('eva_id'))

        # Obtener la evaluación por ID
        response = tabla_evaluaciones.get_item(Key={'evaluacion_id': evaluacion_id})
        evaluacion = response.get('Item')

        if not evaluacion:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': f'Evaluación {evaluacion_id} no encontrada'})
            }

        # Validar que pertenezca a la guía y curso indicados
        if evaluacion.get('guia_id') != guia_id or evaluacion.get('curso_id') != curso_id:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'message': 'La evaluación no pertenece a la guía o curso especificado'})
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'evaluacion': convertir_decimales(evaluacion)})
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
