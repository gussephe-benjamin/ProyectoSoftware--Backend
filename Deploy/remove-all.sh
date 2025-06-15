#!/bin/bash

# Verificar si se pasa un stage, si no se usa "prod" como valor predeterminado
STAGE="${1:-prod}"

# Lista de servicios
SERVICIOS=(
  "USUARIO"
  "CURSO"
  "GUIA"
  "EVALUACION"
  "RANKING"
  "PARTICIPACION"
)

# Ruta base, desde Deploy/ al padre de los servicios
BASE_DIR="../"

# Guardar el directorio de inicio (Deploy/scripts) para regresar allí después de cada eliminación
START_DIR="$(pwd)"

# Función para asegurar que el directorio existe
check_directory() {
  if [ ! -d "$1" ]; then
    echo "Error: El directorio $1 no existe. Abortando."
    exit 1
  fi
}

# Verificar si npx y serverless están instalados
if ! command -v npx &> /dev/null; then
  echo "npx no está instalado. Instalando..."
  npm install -g npx
fi

if ! command -v serverless &> /dev/null; then
  echo "Serverless Framework no está instalado. Instalando..."
  npm install -g serverless
fi

for service in "${SERVICIOS[@]}"
do
  echo "Removing $service from stage $STAGE..."

  # Cambiar al directorio del servicio usando una ruta relativa
  SERVICE_DIR="$BASE_DIR$service"
  check_directory "$SERVICE_DIR"  # Verifica que el directorio existe

  cd "$SERVICE_DIR" || { echo "No se pudo cambiar al directorio $SERVICE_DIR"; exit 1; }

  # Ejecutar remove para el stage especificado
  echo "Removing service $service from stage $STAGE"
  npx serverless remove --stage $STAGE || { echo "Error al eliminar $service en el stage $STAGE"; exit 1; }

  # Volver al directorio base (Deploy/scripts) después de cada eliminación
  cd "$START_DIR" || { echo "Error: No se pudo regresar al directorio base $START_DIR"; exit 1; }
done

echo "=========================================="
echo "   ¡Eliminación completada para todos los servicios!"
echo "=========================================="
