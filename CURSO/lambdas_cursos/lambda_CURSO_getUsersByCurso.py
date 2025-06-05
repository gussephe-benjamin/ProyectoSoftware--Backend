import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tabla_usuarios = dynamodb.Table('Usuario')
tabla_cursos = dynamodb.Table('Curso')  # Agregado para leer el curso

# Para convertir Decimal a int o float en la respuesta
def convertir_decimales(obj):
    if isinstance(obj, list):
        return [convertir_decimales(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convertir_decimales(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        path_params = event.get('pathParameters') or {}
        curso_id = int(path_params.get('id'))

        # 1) Traer el ítem del curso para obtener profesorId y lista de estudiantes
        resp_curso = tabla_cursos.get_item(Key={'curso_id': curso_id})
        if 'Item' not in resp_curso:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Curso no encontrado'})
            }
        curso = resp_curso['Item']

        profesor_id = curso.get('profesorId')
        estudiantes_uids = curso.get('estudiantes', [])

        # 2) Obtener datos del profesor
        resp_prof = tabla_usuarios.get_item(Key={'uid': profesor_id})
        profesor = resp_prof.get('Item')
        if not profesor:
            # Aunque no se espera, si falta el profesor
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'message': 'Profesor asociado no existe'})
            }
        profesor = convertir_decimales(profesor)

        # 3) Obtener datos de cada estudiante
        estudiantes = []
        for uid in estudiantes_uids:
            resp_est = tabla_usuarios.get_item(Key={'uid': uid})
            if 'Item' in resp_est:
                estudiantes.append(convertir_decimales(resp_est['Item']))

        # 4) Devolver profesor y estudiantes
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'curso_id': curso_id,
                'profesor': profesor,
                'estudiantes': estudiantes
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al obtener datos del curso',
                'error': str(e)
            })
        }
