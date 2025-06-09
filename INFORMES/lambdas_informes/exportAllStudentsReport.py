import boto3
import os
import uuid
from collections import defaultdict
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from openpyxl import Workbook

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

participacion_table = dynamodb.Table(os.environ['PARTICIPACION_TABLE'])
evaluacion_table = dynamodb.Table(os.environ['EVALUACION_TABLE'])
estudiante_table = dynamodb.Table(os.environ['ESTUDIANTE_TABLE'])
bucket_name = os.environ['REPORTE_BUCKET']

def lambda_handler(event, context):
    curso_id = event.get("cursoId")
    if not curso_id:
        return {"statusCode": 400, "body": "Falta el campo 'cursoId'"}

    # 1. Obtener evaluaciones del curso
    try:
        evaluaciones_resp = evaluacion_table.scan(
            FilterExpression=Attr("cursoId").eq(curso_id)
        )
        total_evals = len(evaluaciones_resp.get("Items", []))
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar evaluaciones: {str(e)}"}

    # 2. Obtener participaciones del curso
    try:
        participaciones_resp = participacion_table.scan(
            FilterExpression=Attr("cursoId").eq(curso_id)
        )
        participaciones = participaciones_resp.get("Items", [])
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar participaciones: {str(e)}"}

    if not participaciones:
        return {"statusCode": 404, "body": f"No hay participaciones para el curso {curso_id}"}

    # 3. Agrupar por alumno
    alumnos_participaciones = defaultdict(list)
    for item in participaciones:
        alumnos_participaciones[item["alumnoId"]].append(item)

    # 4. Crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen KPIs Alumnos"

    ws.append(["alumnoId", "nombreCompleto", "totalEvals", "promedioNota", "porcentajeEntregas", "rachaAprobaciones"])

    for alumno_id, items in alumnos_participaciones.items():
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

        # Consultar nombre del alumno
        try:
            estudiante_resp = estudiante_table.get_item(Key={"alumnoId": alumno_id})
            nombre = estudiante_resp.get("Item", {}).get("nombreCompleto", "Desconocido")
        except Exception:
            nombre = "Desconocido"

        # Agregar fila
        ws.append([
            alumno_id,
            nombre,
            total_evals,
            round(promedio, 2) if promedio is not None else None,
            round(porcentaje, 2),
            racha
        ])

    # 5. Guardar archivo en /tmp y subir a S3
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
