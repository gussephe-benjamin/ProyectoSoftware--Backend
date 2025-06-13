import json
import boto3
import uuid
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key

# Inicializar cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
tabla_participaciones = dynamodb.Table('Participacion')
tabla_guias = dynamodb.Table('Guia')  

def lambda_handler(event, context):
    try:
        
        # 1) Extraer parámetros del evento (verificar que estos vienen en el body si es un POST)
        body = json.loads(event['body'])  # Si es un POST, deberías obtener los datos del cuerpo
        id_guia = body['id_guia']
        id_alumno = body['uid']
        id_profesor = body['id_profesor']
        id_curso = body['id_curso']
        
    except KeyError as ke:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Falta parámetro obligatorio: {ke}"
            })
        }

    # Generar un nuevo ID para la participación
    id_participacion = uuid.uuid4().hex

    # 2) Obtener datos de la guía desde DynamoDB
    try:
        resultado_guia = tabla_guias.get_item(Key={'id_guia': id_guia})
        if 'Item' not in resultado_guia:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Guía no encontrada"})
            }
        datos_guia = resultado_guia['Item']
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al consultar tabla de Guias",
                "detalle": str(e)
            })
        }

    # 3) Extraer fechas de la guía
    fecha_creacion_guia = datos_guia.get('fecha_creacion')
    fecha_liberacion_guia = datos_guia.get('fecha_liberacion')

    # Validación de fechas
    if not fecha_creacion_guia or not fecha_liberacion_guia:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Faltan fechas en la guía, no se puede registrar participación"
            })
        }

    # 7) Registrar la nueva participación en DynamoDB
    try:
        tabla_participaciones.put_item(
            Item={
                'id_participacion': id_participacion,
                'id_guia': id_guia,
                'id_alumno': id_alumno,
                'id_profesor': id_profesor,
                'id_curso': id_curso,
                'continuidad': None,
                'contador_continuidad': None,
                'fecha_evento_creacion': fecha_creacion_guia,  # o la fecha que corresponda
                'fecha_liberacion': fecha_liberacion_guia,
                'fecha_limite_guia': None,  # Si se debe calcular más adelante, está bien dejarlo como None
                'fecha_entrega_alumno': None
            }
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al insertar participación",
                "detalle": str(e)
            })
        }

    # 8) Devolver la respuesta con éxito
    
    return {
        "statusCode": 201,
        "body": json.dumps({
            "id_participacion": id_participacion,
            "id_guia": id_guia,
            "id_alumno": id_alumno,
            "id_profesor": id_profesor,
            "id_curso": id_curso,
            "fecha_evento_creacion": fecha_creacion_guia,
            "fecha_liberacion": fecha_liberacion_guia
        })
    }
