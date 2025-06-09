import boto3
import os
import uuid
from decimal import Decimal
from collections import defaultdict
from boto3.dynamodb.conditions import Attr
from openpyxl import Workbook

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

participacion_table = dynamodb.Table(os.environ['PARTICIPACION_TABLE'])
evaluacion_table = dynamodb.Table(os.environ['EVALUACION_TABLE'])
curso_table = dynamodb.Table(os.environ['CURSO_TABLE'])
estudiante_table = dynamodb.Table(os.environ['ESTUDIANTE_TABLE'])
bucket_name = os.environ['REPORTE_BUCKET']

def lambda_handler(event, context):
    curso_id = event.get("cursoId")
    if not curso_id:
        return {"statusCode": 400, "body": "Falta el campo 'cursoId'"}

    # Obtener información del curso
    try:
        curso_data = curso_table.get_item(Key={"cursoId": curso_id})
        curso_info = curso_data.get("Item", {})
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al obtener datos del curso: {str(e)}"}

    # Obtener evaluaciones del curso
    try:
        eval_resp = evaluacion_table.scan(FilterExpression=Attr("cursoId").eq(curso_id))
        evaluaciones = eval_resp.get("Items", [])
        total_evals = len(evaluaciones)
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar evaluaciones: {str(e)}"}

    # Obtener participaciones
    try:
        part_resp = participacion_table.scan(FilterExpression=Attr("cursoId").eq(curso_id))
        participaciones = part_resp.get("Items", [])
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar participaciones: {str(e)}"}

    if not participaciones:
        return {"statusCode": 404, "body": f"No hay participaciones para el curso {curso_id}"}

    alumnos_part = defaultdict(list)
    for p in participaciones:
        alumnos_part[p["alumnoId"]].append(p)

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Curso"

    # Encabezado general
    ws.append(["CursoId", curso_id])
    ws.append(["Nombre Curso", curso_info.get("nombre", "Desconocido")])
    ws.append([])
    ws.append(["Resumen por Alumno"])
    ws.append(["alumnoId", "nombreCompleto", "promedioNota", "porcentajeEntregas", "rachaAprobaciones", "totalParticipaciones"])

    # KPIs por alumno
    for alumno_id, parts in alumnos_part.items():
        entregadas, suma, cuenta, racha = 0, Decimal(0), 0, 0

        for p in parts:
            if p.get("entregado"): entregadas += 1
            if p.get("nota") is not None:
                suma += Decimal(str(p["nota"]))
                cuenta += 1

        for p in sorted(parts, key=lambda x: x.get("fechaCreacion", ""), reverse=True):
            if p.get("nota") is not None and Decimal(str(p["nota"])) >= 10:
                racha += 1
            else:
                break

        promedio = float(suma / cuenta) if cuenta > 0 else None
        porcentaje = (entregadas / total_evals) * 100 if total_evals > 0 else 0

        try:
            est_data = estudiante_table.get_item(Key={"alumnoId": alumno_id})
            nombre = est_data.get("Item", {}).get("nombreCompleto", "Desconocido")
        except Exception:
            nombre = "Desconocido"

        ws.append([
            alumno_id,
            nombre,
            round(promedio, 2) if promedio else None,
            round(porcentaje, 2),
            racha,
            len(parts)
        ])

    # Promedio por evaluación
    ws.append([])
    ws.append(["Promedio por Evaluación"])
    ws.append(["evaluacionId", "nombreEvaluacion", "promedioGrupo"])

    eval_notas = defaultdict(list)
    eval_nombres = {e["evaluacionId"]: e.get("nombre", f"Evaluación {i}") for i, e in enumerate(evaluaciones)}

    for p in participaciones:
        if p.get("nota") is not None:
            eval_id = p.get("evaluacionId", "desconocido")
            eval_notas[eval_id].append(float(p["nota"]))

    for eid, notas in eval_notas.items():
        promedio = round(sum(notas) / len(notas), 2)
        ws.append([eid, eval_nombres.get(eid, "Desconocida"), promedio])

    # Guardar archivo en S3
    filename = f"reporte_curso_{curso_id}_{uuid.uuid4().hex[:6]}.xlsx"
    filepath = f"/tmp/{filename}"
    wb.save(filepath)

    try:
        s3.upload_file(
            Filename=filepath,
            Bucket=bucket_name,
            Key=filename,
            ExtraArgs={"ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        )
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al subir a S3: {str(e)}"}

    url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"

    return {
        "statusCode": 200,
        "body": {
            "cursoId": curso_id,
            "urlReporte": url
        }
    }
