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

# Guardar el directorio de inicio (Deploy/scripts) para regresar allí después de cada despliegue
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
  echo "Deploying $service to stage $STAGE..."

  # Cambiar al directorio del servicio usando una ruta relativa
  SERVICE_DIR="$BASE_DIR$service"
  check_directory "$SERVICE_DIR"  # Verifica que el directorio existe

  cd "$SERVICE_DIR" || { echo "No se pudo cambiar al directorio $SERVICE_DIR"; exit 1; }

  # Para ciertos servicios, instalar dependencias si no existen
  if [[ "$service" == "TABLA-PRESTAMOS" || "$service" == "TABLA-SOLICITUD-PRESTAMO" || "$service" == "TABLA-SOPORTE" ]]; then
    if [ ! -f package.json ]; then
      echo "package.json no encontrado. Creando uno nuevo..."
      npm init -y
    fi

    # Verificar si las dependencias están instaladas
    if [ ! -d "node_modules" ]; then
      echo "Running npm install in $service..."
      npm install
    fi

    # Instalar dependencias necesarias si no están presentes
    if ! grep -q "uuid" package.json || ! grep -q "aws-sdk" package.json; then
      echo "Instalando uuid y aws-sdk..."
      npm install uuid aws-sdk
    fi
  fi

  # Ejecutar deploy para el stage especificado
  echo "Deploying service $service to stage $STAGE"
  npx serverless deploy --stage $STAGE || { echo "Error al desplegar $service en el stage $STAGE"; exit 1; }

  # Volver al directorio base (Deploy/scripts) después de cada despliegue
  cd "$START_DIR" || { echo "Error: No se pudo regresar al directorio base $START_DIR"; exit 1; }
done
