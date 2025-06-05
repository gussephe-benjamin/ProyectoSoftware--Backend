import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
tabla_evaluaciones = dynamodb.Table('Evaluacion')
    
def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Obtener curso_id y guia_id desde pathParameters
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))
        guia_id = int(path_params.get('guia_id'))

        evaluacion_id = int(datetime.utcnow().timestamp() * 1000)
        fecha_creacion = datetime.utcnow().isoformat() + 'Z'

        nueva_evaluacion = {
            'evaluacion_id': evaluacion_id,
            'curso_id': curso_id,
            'guia_id': guia_id,
            'contenido': {},  # contenido vacío
            'fechaCreacion': fecha_creacion
        }

        tabla_evaluaciones.put_item(Item=nueva_evaluacion)

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Evaluación creada exitosamente',
                'evaluacion_id': evaluacion_id
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
                'message': 'Error interno al crear la evaluación',
                'error': str(e)
            })
        }
