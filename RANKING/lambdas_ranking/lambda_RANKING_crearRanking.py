import json
import boto3
from boto3.dynamodb.conditions import Key

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb')
tabla_ranking = dynamodb.Table('Ranking')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Obtener parámetros del path
        path_params = event.get('pathParameters') or {}
        curso_id_raw = path_params.get('curso_id')
        uid = path_params.get('uid')

        # Validación básica
        if not curso_id_raw or not uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Faltan curso_id o uid en los parámetros del path'})
            }

        # Asegurarse de que curso_id sea entero si la tabla lo define como Number
        curso_id = int(curso_id_raw)

        # Verificar si ya existe el ranking
        resp = tabla_ranking.get_item(Key={'curso_id': curso_id, 'uid': uid})
        if 'Item' in resp:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Ya existe ranking para este estudiante.'})
            }

        # Crear nuevo ítem con valores iniciales
        nuevo_item = {
            'curso_id': curso_id,
            'uid': uid,
            'guias_completadas': [],
            'puntos': 0,
            'racha': 0,
            'ranking_gsi_pk': curso_id,
            'ranking_gsi_sk': 0
        }

        # Guardar en DynamoDB
        tabla_ranking.put_item(Item=nuevo_item)

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({'message': 'Ranking inicial creado exitosamente.'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
