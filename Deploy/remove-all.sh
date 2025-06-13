#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------
# Script: remove-all.sh
# Propósito: Eliminar todos los servicios Serverless
# Carpeta base: PROYECTOSOFTWARE--BACKEND
# Uso:   ./remove-all.sh [stage]
#   Si no se pasa stage, se usa "prod" por defecto.
# ----------------------------------------------

# 1) Leer el parámetro [stage], o asignar "prod" si no se da.
STAGE="${1:-prod}"

# 2) Misma lista de carpetas que en deploy-all.sh
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

# 4) Guardar directorio inicial para regresar después de cada remove
START_DIR="$(pwd)"

echo ""
echo "=========================================="
echo "  Iniciando eliminación de TODOS los servicios  "
echo "  Stage: $STAGE"
echo "=========================================="
echo ""

for SERVICIO in "${SERVICIOS[@]}"; do
  SERVICE_DIR="$BASE_DIR$SERVICIO"

  echo "------------------------------------------"
  echo " Eliminando recursos de servicio: $SERVICIO"
  echo " Ruta: $SERVICE_DIR"
  echo "------------------------------------------"

  # 4.1) Verificar que la carpeta existe
  if [ ! -d "$SERVICE_DIR" ]; then
    echo "⚠️  Advertencia: El directorio '$SERVICE_DIR' no existe. Se omite este servicio."
    echo ""
    continue
  fi

  # 4.2) Cambiar al directorio del servicio
  cd "$SERVICE_DIR" || { echo "❌ Error: No se pudo entrar a '$SERVICE_DIR'"; exit 1; }

  # 4.3) Ejecutar remove de Serverless
  echo "🗑️  Ejecutando: npx serverless remove --stage $STAGE"
  npx serverless remove --stage "$STAGE" || {
    echo "❌ Error al eliminar '$SERVICIO' en el stage '$STAGE'. Abortando."
    exit 1
  }

  echo "✅ Recursos de '$SERVICIO' eliminados correctamente en stage '$STAGE'."
  echo ""

  # 4.4) Regresar al directorio original (Deploy/)
  cd "$START_DIR" || { echo "❌ Error: No se pudo regresar a '$START_DIR'"; exit 1; }
done

echo "=========================================="
echo "   ¡Eliminación completada para todos los servicios!"
echo "=========================================="
echo ""
