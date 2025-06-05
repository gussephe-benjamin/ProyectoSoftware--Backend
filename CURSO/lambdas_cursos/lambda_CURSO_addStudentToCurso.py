import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
curso_table = dynamodb.Table('Curso')
usuario_table = dynamodb.Table('Usuario')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*'
    }

    try:
        curso_id = int(event['pathParameters'].get('id'))
        body = json.loads(event['body'])
        correos = body.get('emails', [])

        if not curso_id or not isinstance(correos, list) or len(correos) == 0:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Se requiere cursoId en el path y una lista de emails en el body'
                })
            }

        # Buscar uids por correo
        uids_encontrados = []
        no_encontrados = []
        for email in correos:
            response = usuario_table.query(
                IndexName='email_index',
                KeyConditionExpression=Key('email').eq(email)
            )
            items = response.get('Items', [])
            if items:
                uids_encontrados.append(items[0]['uid'])
            else:
                no_encontrados.append(email)

        if not uids_encontrados:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Ningún correo corresponde a un usuario registrado'})
            }

        # Obtener el curso actual
        curso_response = curso_table.get_item(Key={'curso_id': curso_id})
        curso = curso_response.get('Item')

        if not curso:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Curso no encontrado'})
            }

        estudiantes_actuales = set(curso.get('estudiantes', []))
        nuevos_uids = [uid for uid in uids_encontrados if uid not in estudiantes_actuales]

        if not nuevos_uids:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Ningún estudiante nuevo para agregar',
                    'uids_ya_presentes': list(estudiantes_actuales),
                    'emails_no_encontrados': no_encontrados
                })
            }

        # Actualizar el curso con los nuevos estudiantes
        curso_table.update_item(
            Key={'curso_id': curso_id},
            UpdateExpression='''
                SET estudiantes = list_append(if_not_exists(estudiantes, :vacio), :nuevos),
                    totalEstudiantes = if_not_exists(totalEstudiantes, :cero) + :incremento
            ''',
            ExpressionAttributeValues={
                ':vacio': [],
                ':nuevos': nuevos_uids,
                ':cero': 0,
                ':incremento': len(nuevos_uids)
            },
            ReturnValues='UPDATED_NEW'
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Estudiantes agregados correctamente',
                'uids_agregados': nuevos_uids,
                'emails_no_encontrados': no_encontrados
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al agregar estudiantes',
                'error': str(e)
            })
        }
