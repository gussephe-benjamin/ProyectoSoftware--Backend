import json
import uuid
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Curso')

def lambda_handler(event, context):
    # Configuración de headers para CORS
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # Parsear el cuerpo de la solicitud
        request_body = json.loads(event['body'])
        
        # Validar campos obligatorios
        required_fields = ['nombre', 'profesorId']
        if not all(field in request_body for field in required_fields):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Campos requeridos faltantes',
                    'required_fields': required_fields
                })
            }
        
        # Generar IDs y timestamps
        curso_id = int(datetime.utcnow().timestamp() * 1000)
        fecha_actual = datetime.utcnow().isoformat() + 'Z'
        
        # Estructura básica del curso
        nuevo_curso = {
            'curso_id': curso_id,
            'nombre': request_body['nombre'],
            'profesorId': request_body['profesorId'],
            'fechaCreacion': fecha_actual,
            'totalEstudiantes': 0,  # Inicialmente sin estudiantes
            'guias': []
        }
        
    
        # Insertar en DynamoDB
        try:
            response = table.put_item(
                Item=nuevo_curso,
                ConditionExpression='attribute_not_exists(cursoId)'  # Evitar sobrescritura
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 409,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'El curso ya existe (ID duplicado)'
                    })
                }
            raise
        
        # Respuesta exitosa
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Curso creado exitosamente'
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'message': 'Formato JSON inválido en el cuerpo de la solicitud'
            })
        }
    except Exception as e:
        print(f"Error al crear curso: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error interno al crear el curso',
                'error': str(e)
            })
        }