import json
import boto3
import uuid
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key

# Función auxiliar para sumar 24 horas a una fecha ISO 8601 con “Z”
def sumar_24_horas_fecha(fecha_original):
    try:
        if fecha_original.endswith("Z"):
            # Convertir "2025-06-10T14:30:00Z" → "2025-06-10T14:30:00+00:00"
            fecha_corregida = fecha_original[:-1] + "+00:00"
        else:
            fecha_corregida = fecha_original

        fecha_evento = datetime.fromisoformat(fecha_corregida)
        # fecha_evento ahora tiene tzinfo=UTC
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Formato de fecha inválido. Debe ser ISO 8601 con 'Z', p.ej. '2025-06-10T14:30:00Z'.",
                "detalle": str(e)
            })
        }

    fecha_mas_24 = fecha_evento + timedelta(hours=24)
    fecha_mas_24_utc = fecha_mas_24.astimezone(timezone.utc)
    return fecha_mas_24_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


# Inicializar cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
tabla_participaciones = dynamodb.Table('t_PARTICIPACION')
tabla_guias = dynamodb.Table('t_GUIA')  # <-- corregido: apuntar a la tabla de guías

INDEX_ALUMNO_FECHA = "participaciones_por_alumno"  # Asegúrate que coincida con el nombre real del GSI


def lambda_handler(event, context):
    # 1) Extraer parámetros del evento
    try:
        id_guia = event['id_guia']
        id_alumno = event['id_alumno']
        id_profesor = event['id_profesor']
        id_curso = event['id_curso']
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
    fecha_entrega_guia_alumno = datos_guia.get('fecha_entrega_alumno')
    fecha_limite_guia1 = datos_guia.get('fecha_limite')

    # Validar que existan las fechas necesarias
    if not (fecha_liberacion_guia and fecha_entrega_guia_alumno and fecha_limite_guia1):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Faltan fechas obligatorias en el ítem de guía"
            })
        }

    # 4) Calcular fecha límite alternativa (liberación + 24h)
    fecha_limite_guia2 = sumar_24_horas_fecha(fecha_liberacion_guia)
    if isinstance(fecha_limite_guia2, dict):
        # Si sumar_24_horas_fecha devolvió un dict, es un error
        return fecha_limite_guia2

    # 5) Determinar si la entrega del alumno está dentro del rango permitido
    #    Se comparan las cadenas ISO directamente; se asume que están en el mismo formato “YYYY-MM-DDTHH:MM:SSZ”
    if fecha_liberacion_guia <= fecha_entrega_guia_alumno <= fecha_limite_guia1:
        continuidad = True
    else:
        continuidad = False

    # 6) Contar cuántas participaciones consecutivas con continuidad == True ha tenido este alumno
    contador_continuidad = 0
    last_key = None

    while True:
        try:
            if last_key:
                response = tabla_participaciones.query(
                    IndexName=INDEX_ALUMNO_FECHA,
                    KeyConditionExpression=Key("id_alumno").eq(id_alumno),
                    ScanIndexForward=True, # primero lo primero y despues lo ultimos en la tabla
                    ExclusiveStartKey=last_key
                )
            else:
                response = tabla_participaciones.query(
                    IndexName=INDEX_ALUMNO_FECHA,
                    KeyConditionExpression=Key("id_alumno").eq(id_alumno),
                    ScanIndexForward= True 
                )
        
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Error al consultar participaciones",
                    "detalle": str(e)
                })
            }

        items = response.get('Items', [])
        for item in items:
            if not item.get('continuidad', False):
                # Encontramos una participación con continuidad False → detenemos el conteo
                last_key = None
                break
            contador_continuidad += 1

        # Si Break por encontrar False, salimos del while
        if not response.get('LastEvaluatedKey') or (items and not items[-1].get('continuidad', False)):
            break

        last_key = response['LastEvaluatedKey']

    # 7) Registrar la nueva participación en DynamoDB
    try:
        tabla_participaciones.put_item(
            Item={
                'id_participacion': id_participacion,
                'id_guia': id_guia,
                'id_alumno': id_alumno,
                'id_profesor': id_profesor,
                'id_curso': id_curso,
                'continuidad': continuidad,
                'contador_continuidad': contador_continuidad,
                'fecha_evento': fecha_creacion_guia  # o la fecha que corresponda
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
            "continuidad": continuidad,
            "contador_continuidad": contador_continuidad,
            "fecha_evento": fecha_creacion_guia
        })
    }
