import boto3
import os
from collections import defaultdict
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
participacion_table = dynamodb.Table(os.environ['PARTICIPACION_TABLE'])
evaluacion_table = dynamodb.Table(os.environ['EVALUACION_TABLE'])

def lambda_handler(event, context):
    curso_id = event.get("cursoId")
    if not curso_id:
        return {"statusCode": 400, "body": "Falta el campo 'cursoId'"}

    # 1. Obtener total de evaluaciones del curso
    try:
        evaluaciones_resp = evaluacion_table.scan(
            FilterExpression=Attr("cursoId").eq(curso_id)
        )
        total_evals = len(evaluaciones_resp.get("Items", []))
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar evaluaciones: {str(e)}"}

    # 2. Obtener todas las participaciones del curso
    try:
        participaciones_resp = participacion_table.scan(
            FilterExpression=Attr("cursoId").eq(curso_id)
        )
        participaciones = participaciones_resp.get("Items", [])
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar participaciones: {str(e)}"}

    if not participaciones:
        return {"statusCode": 404, "body": f"No hay participaciones para el curso {curso_id}"}

    # 3. Agrupar participaciones por alumno
    alumnos = defaultdict(list)
    for item in participaciones:
        alumnos[item["alumnoId"]].append(item)

    resumen = []

    for alumno_id, items in alumnos.items():
        total_entregadas = 0
        suma_notas = Decimal(0)
        cuenta_notas = 0
        racha = 0

        for p in items:
            if p.get("entregado"):
                total_entregadas += 1

            nota = p.get("nota")
            if nota is not None:
                suma_notas += Decimal(str(nota))
                cuenta_notas += 1

        for p in sorted(items, key=lambda x: x.get("fechaCreacion", ""), reverse=True):
            nota = p.get("nota")
            if nota is not None and Decimal(str(nota)) >= 10:
                racha += 1
            else:
                break

        promedio = float(suma_notas / cuenta_notas) if cuenta_notas > 0 else None
        porcentaje = (total_entregadas / total_evals) * 100 if total_evals > 0 else 0

        resumen.append({
            "alumnoId": alumno_id,
            "totalEvals": total_evals,
            "promedioNota": promedio,
            "porcentajeEntregas": round(porcentaje, 2),
            "rachaAprobaciones": racha
        })

    return {
        "statusCode": 200,
        "body": resumen
    }
