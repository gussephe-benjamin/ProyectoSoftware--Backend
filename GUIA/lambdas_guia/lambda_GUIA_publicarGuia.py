import json
import boto3

dynamodb = boto3.resource('dynamodb')
tabla_guias = dynamodb.Table('Guia')

def lambda_handler(event, context):
    headers = {'Content-Type': 'application/json'}

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))
        guia_id = int(path_params.get('guia_id'))

        # Obtener la guía primero
        response = tabla_guias.get_item(Key={'guia_id': guia_id})
        guia = response.get('Item')

        if not guia:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': f'Guía {guia_id} no encontrada'})
            }

        # Verificar si pertenece al curso dado
        if guia['curso_id'] != curso_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': f'La guía {guia_id} no pertenece al curso {curso_id}'})
            }

        # Actualizar guía: marcar como publicada
        tabla_guias.update_item(
            Key={'guia_id': guia_id},
            UpdateExpression='SET publicado = :val',
            ExpressionAttributeValues={':val': True}
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': f'Guía {guia_id} publicada correctamente'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
