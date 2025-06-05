import json
import boto3

dynamodb = boto3.resource('dynamodb')
curso_table = dynamodb.Table('Curso')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))
        uid = path_params.get('user_id')

        if not curso_id or not uid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Se requiere curso_id y uid en el path'})
            }

        # Obtener curso actual
        curso_resp = curso_table.get_item(Key={'curso_id': curso_id})
        curso = curso_resp.get('Item')

        if not curso:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Curso no encontrado'})
            }

        estudiantes = curso.get('estudiantes', [])
        if uid not in estudiantes:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'El estudiante no está en el curso'})
            }

        # Eliminar al estudiante de la lista
        
        nuevos_estudiantes = [e for e in estudiantes if e != uid]
        nuevo_total = max(0, curso.get('totalEstudiantes', 0) - 1)

        # Actualizar tabla
        curso_table.update_item(
            Key={'curso_id': curso_id},
            UpdateExpression='SET estudiantes = :est, totalEstudiantes = :total',
            ExpressionAttributeValues={
                ':est': nuevos_estudiantes,
                ':total': nuevo_total
            }
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Estudiante eliminado correctamente',
                'uid_eliminado': uid
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al eliminar estudiante del curso',
                'error': str(e)
            })
        }
