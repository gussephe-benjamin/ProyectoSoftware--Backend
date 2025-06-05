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
        # Obtener curso_id y uid del path
        path_params = event.get('pathParameters') or {}
        uid = path_params.get('uid')

        try:
            curso_id = int(path_params.get('curso_id'))
        except (TypeError, ValueError):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'curso_id inválido, debe ser un número'})
            }

        if not uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Falta parámetro uid'})
            }

        # Obtener guia_id y puntos_obtenidos del body
        body = json.loads(event['body'])
        guia_id = body.get('guia_id')
        puntos_obtenidos = body.get('puntos_obtenidos')

        if not guia_id or puntos_obtenidos is None:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Faltan guia_id o puntos_obtenidos en el cuerpo'})
            }

        # Buscar ranking
        response = tabla_ranking.get_item(Key={'curso_id': curso_id, 'uid': uid})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Ranking no encontrado para este estudiante y curso.'})
            }

        # Verificar si la guía ya fue completada
        guias_completadas = item.get('guias_completadas', [])
        if guia_id in guias_completadas:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Guía ya registrada como completada.'})
            }

        # Actualizar puntos, racha y lista de guías
        nuevos_puntos = item.get('puntos', 0) + puntos_obtenidos
        guias_completadas.append(guia_id)
        nueva_racha = len(guias_completadas)

        # Actualizar en DynamoDB
        tabla_ranking.update_item(
            Key={'curso_id': curso_id, 'uid': uid},
            UpdateExpression="""
                SET puntos = :p,
                    guias_completadas = :g,
                    racha = :r,
                    ranking_gsi_sk = :gsi
            """,
            ExpressionAttributeValues={
                ':p': nuevos_puntos,
                ':g': guias_completadas,
                ':r': nueva_racha,
                ':gsi': -nuevos_puntos  # Para ranking descendente en GSI
            }
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'Ranking actualizado correctamente.'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
