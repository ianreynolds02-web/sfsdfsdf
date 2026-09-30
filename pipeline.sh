#!/usr/bin/env bash
# Flujo completo: Gemini analiza el video -> cortes.json -> ffmpeg arma salida.mp4
#
# Uso: ./pipeline.sh video.mp4 [opciones de analizar.py]
#   ./pipeline.sh clase.mp4 --objetivo "quitar silencios y muletillas"
#
# Puedes revisar/editar cortes.json antes de aplicar: usa SOLO_ANALIZAR=1
set -euo pipefail
cd "$(dirname "$0")"

[[ $# -ge 1 ]] || { echo "Uso: $0 video.mp4 [opciones de analizar.py]" >&2; exit 1; }
VIDEO="$1"; shift

python3 analizar.py "$VIDEO" "$@"

if [[ "${SOLO_ANALIZAR:-0}" == "1" ]]; then
  echo "Revisa cortes.json y luego: python3 aplicar_cortes.py \"$VIDEO\"" >&2
  exit 0
fi

python3 aplicar_cortes.py "$VIDEO"
