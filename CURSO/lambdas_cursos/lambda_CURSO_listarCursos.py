import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Curso')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)  # sin .0
        else:
            return float(obj)  # con .decimal si lo necesita
    raise TypeError

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', 10))
        last_evaluated_key = query_params.get('lastEvaluatedKey')
        
        scan_params = {'Limit': limit}
        if last_evaluated_key:
            scan_params['ExclusiveStartKey'] = json.loads(last_evaluated_key)
        
        response = table.scan(**scan_params)
        
        response_data = {
            'cursos': response['Items'],
            'count': len(response['Items'])
        }
        
        if 'LastEvaluatedKey' in response:
            response_data['lastEvaluatedKey'] = json.dumps(response['LastEvaluatedKey'], default=decimal_default)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error al listar cursos: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error al listar cursos',
                'error': str(e)
            })
        }
