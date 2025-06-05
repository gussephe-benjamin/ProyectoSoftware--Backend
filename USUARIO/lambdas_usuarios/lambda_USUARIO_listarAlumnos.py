def lambda_handler(event, context):
    """
    Función Lambda “vacía” que no hace nada por ahora.
    En el futuro puedes agregar tu lógica aquí.
    """
    # Simplemente retornamos un 200 con un mensaje vacío
    return {
        "statusCode": 200,
        "body": ""
    }