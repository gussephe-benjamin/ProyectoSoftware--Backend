import boto3
import os
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')

participacion_table = dynamodb.Table(os.environ['PARTICIPACION_TABLE'])
evaluacion_table = dynamodb.Table(os.environ['EVALUACION_TABLE'])
curso_table = dynamodb.Table(os.environ['CURSO_TABLE'])
estudiante_table = dynamodb.Table(os.environ['ESTUDIANTE_TABLE'])

def lambda_handler(event, context):
    alumno_id = event.get("alumnoId")
    curso_id = event.get("cursoId")

    if not alumno_id or not curso_id:
        return {"statusCode": 400, "body": "Falta alumnoId o cursoId"}

    # 1. Obtener evaluaciones del curso
    try:
        eval_resp = evaluacion_table.scan(FilterExpression=Attr("cursoId").eq(curso_id))
        evaluaciones = eval_resp.get("Items", [])
        total_evals = len(evaluaciones)
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar evaluaciones: {str(e)}"}

    # 2. Obtener participaciones del curso
    try:
        part_resp = participacion_table.scan(FilterExpression=Attr("cursoId").eq(curso_id))
        participaciones = part_resp.get("Items", [])
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar participaciones: {str(e)}"}

    if not participaciones:
        return {"statusCode": 404, "body": f"No hay participaciones para el curso {curso_id}"}

    # 3. Agrupar participaciones por alumno
    alumnos_part = defaultdict(list)
    for p in participaciones:
        alumnos_part[p["alumnoId"]].append(p)

    # 4. Calcular KPIs del alumno
    alumno_parts = alumnos_part.get(alumno_id, [])
    entregadas = 0
    suma = Decimal(0)
    cuenta = 0
    racha = 0

    for p in alumno_parts:
        if p.get("entregado"): entregadas += 1
        if p.get("nota") is not None:
            suma += Decimal(str(p["nota"]))
            cuenta += 1

    for p in sorted(alumno_parts, key=lambda x: x.get("fechaCreacion", ""), reverse=True):
        if p.get("nota") is not None and Decimal(str(p["nota"])) >= 10:
            racha += 1
        else:
            break

    promedio_alumno = float(suma / cuenta) if cuenta > 0 else None
    porcentaje = (entregadas / total_evals) * 100 if total_evals > 0 else 0

    # 5. Comparativo grupal
    alumnos_promedios = []
    for aid, parts in alumnos_part.items():
        s, c = Decimal(0), 0
        for p in parts:
            if p.get("nota") is not None:
                s += Decimal(str(p["nota"]))
                c += 1
        if c > 0:
            alumnos_promedios.append((aid, float(s / c)))

    alumnos_promedios.sort(key=lambda x: x[1], reverse=True)
    promedio_grupo = sum(p[1] for p in alumnos_promedios) / len(alumnos_promedios) if alumnos_promedios else 0

    ranking = next((i+1 for i, (aid, _) in enumerate(alumnos_promedios) if aid == alumno_id), None)

    # 6. Promedio por evaluación (para gráficas)
    eval_promedios = defaultdict(list)
    for p in participaciones:
        if p.get("nota") is not None:
            eval_id = p.get("evaluacionId", "desconocido")
            eval_promedios[eval_id].append(float(p["nota"]))

    promedio_por_eval = {
        eid: round(sum(notas) / len(notas), 2)
        for eid, notas in eval_promedios.items()
    }

    return {
        "statusCode": 200,
        "body": {
            "alumnoId": alumno_id,
            "cursoId": curso_id,
            "statsAlumno": {
                "promedioNota": promedio_alumno,
                "totalParticipaciones": len(alumno_parts),
                "porcentajeEntregas": round(porcentaje, 2),
                "rachaAprobaciones": racha
            },
            "statsGrupo": {
                "promedioGeneralGrupo": round(promedio_grupo, 2),
                "rankingAlumno": ranking,
                "promedioPorEvaluacion": promedio_por_eval
            }
        }
    }
