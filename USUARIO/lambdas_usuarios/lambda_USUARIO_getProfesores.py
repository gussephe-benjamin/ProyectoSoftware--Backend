import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
usuario_table = dynamodb.Table('t_Usuario')

def lambda_handler(event, context):
    
    response = usuario_table.scan(
        FilterExpression=Key('role').eq('profesor')
    )
    return {
        'statusCode': 200,
        'body': json.dumps(response['Items'])
    }