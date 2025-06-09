import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
participacion_table = dynamodb.Table(os.environ['PARTICIPACION_TABLE'])
evaluacion_table = dynamodb.Table(os.environ['EVALUACION_TABLE'])

def lambda_handler(event, context):
    alumno_id = event.get("alumnoId")
    if not alumno_id:
        return {
            "statusCode": 400,
            "body": "Falta el campo alumnoId"
        }

    # 1. Obtener todas las participaciones del alumno
    response = participacion_table.query(
        IndexName='participaciones_por_alumno',
        KeyConditionExpression=Key('alumnoId').eq(alumno_id),
        ScanIndexForward=True  # orden por fechaCreacion
    )
    participaciones = response.get("Items", [])

    if not participaciones:
        return {
            "statusCode": 404,
            "body": f"No hay participaciones para el alumno {alumno_id}"
        }

    # 2. Suponemos que todas las participaciones del alumno son del mismo curso
    curso_id = participaciones[0].get("cursoId")
    if not curso_id:
        return {
            "statusCode": 500,
            "body": "No se pudo determinar el cursoId desde las participaciones"
        }

    # 3. Contar todas las evaluaciones del curso
    try:
        evaluaciones_resp = evaluacion_table.scan(
            FilterExpression="cursoId = :cid",
            ExpressionAttributeValues={":cid": curso_id}
        )
        total_evals = len(evaluaciones_resp.get("Items", []))
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error al consultar evaluaciones: {str(e)}"
        }

    # 4. Calcular métricas desde participaciones
    total_entregadas = 0
    suma_notas = Decimal(0)
    cuenta_notas = 0
    racha_aprobaciones = 0

    for item in participaciones:
        if item.get("entregado") is True:
            total_entregadas += 1

        nota = item.get("nota")
        if nota is not None:
            suma_notas += Decimal(str(nota))
            cuenta_notas += 1

    # 5. Calcular racha de aprobaciones desde el más reciente hacia atrás
    for item in reversed(participaciones):
        nota = item.get("nota")
        if nota is not None and Decimal(str(nota)) >= 10:
            racha_aprobaciones += 1
        else:
            break

    promedio = float(suma_notas / cuenta_notas) if cuenta_notas > 0 else None
    porcentaje_entregas = (total_entregadas / total_evals) * 100 if total_evals > 0 else 0

    return {
        "statusCode": 200,
        "body": {
            "alumnoId": alumno_id,
            "cursoId": curso_id,
            "totalEvals": total_evals,
            "promedioNota": promedio,
            "porcentajeEntregas": round(porcentaje_entregas, 2),
            "rachaAprobaciones": racha_aprobaciones
        }
    }
