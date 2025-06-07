import json 
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal


def decimal_to_float(items):
    for item in items:
        for key in item:
            if isinstance(item[key], Decimal):
                item[key] = float(item[key])
    return items

def  lambda_handler(event,context):
    
    body = event["body"]
    
    alumno_uid = body["alumno_id"]
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Participacion')
    
    response = table.scan(
        FilterExpression=Key('alumno_uid').eq(alumno_uid)
    )
    
    items = response.get('Items', [])
    
    items = decimal_to_float(items)
    
    return {
        "statusCode": 200,
        "Participaciones del alumno con id:": alumno_uid,
        "body": json.dumps(items)
    }
    