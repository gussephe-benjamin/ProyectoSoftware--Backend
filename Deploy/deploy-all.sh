#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------
# Script: deploy-all.sh
# Propósito: Desplegar todos los servicios Serverless
# Carpeta base: PROYECTOSOFTWARE--BACKEND
# Uso:   ./deploy-all.sh [stage]
#   Si no se pasa stage, se usa "prod" por defecto.
# ----------------------------------------------

# 1) Leer el parámetro [stage], o asignar "prod" si no se da.
STAGE="${1:-prod}"

# 2) Misma lista de carpetas que en remove-all.sh
SERVICIOS=(
  "USUARIO"
  "CURSO"
  "GUIA"
  "EVALUACION"
  "RANKING"
  "PARTICIPACION"
)

# 3) Ruta base, desde Deploy/ al padre de los servicios
BASE_DIR="../"

# 4) Guardar directorio inicial para regresar después de cada deploy
START_DIR="$(pwd)"

# 5) Dirección SSH del servidor donde se van a desplegar los servicios
# Puedes modificar esta dirección a la de tu servidor o usar variables de entorno para los accesos.
# Usando SSH para desplegar en el servidor remoto
REMOTE_SERVER="ssh -i ./.ssh/labsuser.pem ubuntu@3.86.183.138"

echo ""
echo "=========================================="
echo "  Iniciando despliegue de TODOS los servicios  "
echo "  Stage: $STAGE"
echo "=========================================="
echo ""

for SERVICIO in "${SERVICIOS[@]}"; do
  SERVICE_DIR="$BASE_DIR$SERVICIO"

  echo "------------------------------------------"
  echo " Desplegando recursos de servicio: $SERVICIO"
  echo " Ruta: $SERVICE_DIR"
  echo "------------------------------------------"

  # 6) Verificar que la carpeta exista
  if [ ! -d "$SERVICE_DIR" ]; then
    echo "⚠️  Advertencia: El directorio '$SERVICE_DIR' no existe. Se omite este servicio."
    echo ""
    continue
  fi

  # 7) Conectar por SSH al servidor y ejecutar el despliegue
  echo "🔑  Conectando al servidor remoto para desplegar: $SERVICIO"
  ssh "$REMOTE_SERVER" <<EOF
    cd "$SERVICE_DIR" || exit 1
    echo "🗂️  Desplegando $SERVICIO en el servidor"
    npx serverless deploy --stage "$STAGE" || { echo "❌ Error al desplegar '$SERVICIO' en el stage '$STAGE'."; exit 1; }
    echo "✅ Despliegue de '$SERVICIO' completado correctamente en stage '$STAGE'."
EOF

  echo ""

done

echo "=========================================="
echo "   ¡Despliegue completado para todos los servicios!"
echo "=========================================="
echo ""
