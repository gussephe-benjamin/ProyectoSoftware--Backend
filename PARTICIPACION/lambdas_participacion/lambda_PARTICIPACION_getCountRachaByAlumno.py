import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
tabla_participaciones = dynamodb.Table("t_PARTICIPACION")

# Nombre del GSI que indexa por alumno y fecha_evento
INDEX_ALUMNO_FECHA = "participaciones_por_alumno"

def lambda_handler(event, context):
    """
    Devuelve la racha actual de un alumno en un curso dado,
    es decir, el número de participaciones consecutivas con continuidad == True
    empezando por la más reciente hasta encontrar la primera False.
    
    Se espera un payload JSON:
      {
        "alumno": "<alumnoId>",
        "curso":  "<cursoId>"
      }
    """
    # 1) Obtener parámetros
    alumno_id = event.get("alumno")
    curso_id  = event.get("curso")
    if not alumno_id or not curso_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Se requieren 'alumno' y 'curso' en el cuerpo del request"
            })
        }
    
    # 2) Query al GSI: particiones por alumno, orden descendente (más reciente primero)
    contador_racha = 0
    last_key = None
    
    while True:
        try:
            kwargs = {
                "IndexName": INDEX_ALUMNO_FECHA,
                "KeyConditionExpression": Key("alumno").eq(alumno_id),
                "ScanIndexForward": False,    # False => orden descendente
                "FilterExpression": Key("curso").eq(curso_id)
            }
            if last_key:
                kwargs["ExclusiveStartKey"] = last_key
            
            resp = tabla_participaciones.query(**kwargs)
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Error al consultar participaciones",
                    "detalle": str(e)
                })
            }
        
        items = resp.get("Items", [])
        # 3) Recorrer items en orden descendente
        for item in items:
            if not item.get("continuidad", False):
                # primera interrupción, retornamos el contador actual
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "alumno": alumno_id,
                        "curso": curso_id,
                        "rachaActual": contador_racha
                    })
                }
            contador_racha += 1
        
        # 4) Si hay más páginas, continuar; si no, romper
        if "LastEvaluatedKey" in resp:
            last_key = resp["LastEvaluatedKey"]
        else:
            break
    
    # 5) Si nunca encontramos un False, devolvemos el total contado
    return {
        "statusCode": 200,
        "body": json.dumps({
            "alumno": alumno_id,
            "curso": curso_id,
            "rachaActual": contador_racha
        })
    }
