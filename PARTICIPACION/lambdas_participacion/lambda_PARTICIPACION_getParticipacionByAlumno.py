import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# Conexión a DynamoDB
dynamodb = boto3.resource("dynamodb")
tabla_participaciones = dynamodb.Table("t_PARTICIPACION")

# Nombre del GSI que indexa por alumno y fecha_evento
INDEX_ALUMNO_FECHA = "participaciones_por_alumno"

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)

def lambda_handler(event, context):
    
    """
    Retorna todas las participaciones de un alumno ordenadas por fecha de evento (ascendente).
    Se espera un body JSON:
      {
        "alumno": "<alumnoId>"
      }
    """

    # 1) Parsear body como JSON
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Formato JSON inválido en el body"})
        }

    alumno_id = body.get("alumno")
    if not alumno_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Falta el campo 'alumno' en el body"})
        }

    # 2) Query al GSI para traer participaciones ordenadas por fecha_evento ascendente
    try:
        resp = tabla_participaciones.query(
            IndexName=INDEX_ALUMNO_FECHA,
            KeyConditionExpression=Key("alumno").eq(alumno_id),
            ScanIndexForward=True  # True => orden ascendente (más antiguo primero)
        )
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al consultar DynamoDB",
                "detalle": str(e)
            })
        }

    items = resp.get("Items", [])

    # 3) Construir y devolver la respuesta
    return {
        "statusCode": 200,
        "body": json.dumps({
            "alumno": alumno_id,
            "participaciones": items
        }, cls=DecimalEncoder)
    }
