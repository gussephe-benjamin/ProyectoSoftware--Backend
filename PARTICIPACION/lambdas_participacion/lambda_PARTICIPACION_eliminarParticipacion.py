import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
tabla_participaciones = dynamodb.Table("t_PARTICIPACION")

def lambda_handler(event, context):
    
    """
    Elimina una participación en base a su id_participacion.
    Se espera un body JSON con:
      {
        "id_participacion": "<participacionId>"
      }
    """

    # 1) Parsear body JSON
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "JSON inválido en el body"})
        }

    # 2) Obtener id_participacion
    id_part = body.get("id_participacion")
    if not id_part:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Falta 'id_participacion' en el body"})
        }

    # 3) Intentar eliminar el ítem
    try:
        response = tabla_participaciones.delete_item(
            Key={"id_participacion": id_part},
            ConditionExpression="attribute_exists(id_participacion)"
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ConditionalCheckFailedException":
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Participación no encontrada"})
            }
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al eliminar participación",
                "detalle": str(e)
            })
        }

    # 4) Responder con éxito
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Participación '{id_part}' eliminada correctamente"
        })
    }