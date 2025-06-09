import boto3
import os
import uuid
from boto3.dynamodb.conditions import Key
from openpyxl import Workbook

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

participacion_table = dynamodb.Table(os.environ['PARTICIPACION_TABLE'])
estudiantes_table = dynamodb.Table(os.environ['ESTUDIANTE_TABLE'])  # <-- nueva tabla
bucket_name = os.environ['REPORTE_BUCKET']

def lambda_handler(event, context):
    alumno_id = event.get("alumnoId")
    if not alumno_id:
        return {"statusCode": 400, "body": "Falta el campo 'alumnoId'"}

    # Obtener datos del alumno desde tabla estudiante
    alumno_info = {}
    try:
        alumno_data = estudiantes_table.get_item(Key={"alumnoId": alumno_id})
        alumno_info = alumno_data.get("Item", {})
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al obtener datos del alumno: {str(e)}"}

    # Obtener participaciones
    try:
        response = participacion_table.query(
            IndexName='participaciones_por_alumno',
            KeyConditionExpression=Key('alumnoId').eq(alumno_id),
            ScanIndexForward=True
        )
        items = response.get("Items", [])
    except Exception as e:
        return {"statusCode": 500, "body": f"Error al consultar participaciones: {str(e)}"}

    if not items:
        return {"statusCode": 404, "body": f"No hay participaciones para el alumno {alumno_id}"}

    # Crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Participaciones"

    # Escribir info del alumno
    ws.append(["AlumnoId", alumno_id])
    ws.append(["Nombre", alumno_info.get("nombreCompleto", "Desconocido")])
    ws.append(["Curso", alumno_info.get("curso", "N/A")])
    ws.append([])
    ws.append(["Participaciones"])
    ws.append(["participacionId", "fechaCreacion", "nota", "entregado"])

    # Agregar participaciones
    for item in items:
        ws.append([
            item.get("participacionId", ""),
            item.get("fechaCreacion", ""),
            item.get("nota", ""),
            item.get("entregado", False)
        ])

    # Guardar Excel y subir a S3
    filename = f"reporte_{alumno_id}_{uuid.uuid4().hex[:6]}.xlsx"
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
            "alumnoId": alumno_id,
            "urlReporte": url
        }
    }
