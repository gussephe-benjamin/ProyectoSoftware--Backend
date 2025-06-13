import json
import boto3
import uuid
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
tabla_participaciones = dynamodb.Table('Participacion')
tabla_usuarios = dynamodb.Table('Usuario')

INDEX_ALUMNO_FECHA = "participaciones_por_alumno"  

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

def lambda_handler(event, context):
    
    # 1) Extraer parámetros del evento
    
    body = json.loads(event['body'])  # Asumiendo que los parámetros vienen en el cuerpo de la solicitud
    id_guia = body['id_guia']
    fecha_entrega_alumno = body['fecha_entrega_alumno']

    # 2) Obtener datos de la guía desde DynamoDB

    resultado_guia = tabla_participaciones.get_item(Key={'id_guia': id_guia})
    
    datos_guia = resultado_guia['Item']
    
    fecha_liberacion_guia = datos_guia.get('fecha_liberacion_guia')

    id_alumno = datos_guia.get('id_alumno')
    
    fecha_limite_guia = sumar_24_horas_fecha(fecha_entrega_alumno)
    
    
    # 3) Actualizar la fecha de entrega de las fechas de la participación 

    tabla_participaciones.update_item(
        Key={'id_guia': id_guia},
        UpdateExpression='SET fecha_entrega_alumno = :fecha_entrega_alumno',
        ExpressionAttributeValues={
            ':fecha_entrega_alumno': fecha_entrega_alumno
        }
    )

    tabla_participaciones.update_item(
        Key={'id_guia': id_guia},
        UpdateExpression='SET fecha_limite_guia = :fecha_limite_guia',
        ExpressionAttributeValues={
            ':fecha_limite_guia': fecha_limite_guia
        }
    )
    
    # 4) calcular continuidad del estudiante

    if fecha_liberacion_guia <= fecha_entrega_alumno <= fecha_limite_guia:
        continuidad = True
    else:
        continuidad = False

     # 5) Contar cuántas participaciones consecutivas con continuidad == True ha tenido este alumno
     
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

    # 6) Registrar la nueva participación en DynamoDB
        
    try:
        tabla_participaciones.put_item(
            Item={           
                'id_guia': id_guia,
                'continuidad': continuidad,
                'contador_continuidad': contador_continuidad,
                'fecha_entrega_alumno': fecha_entrega_alumno,
                'fecha_limite_guia': fecha_limite_guia
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

        