#!/usr/bin/env python3
"""Paso 1: Gemini mira el video y devuelve los tramos a conservar en cortes.json.

Uso:
    export GEMINI_API_KEY=...            # https://aistudio.google.com/apikey
    python3 analizar.py video.mp4
    python3 analizar.py video.mp4 --objetivo "quitar silencios y muletillas" --max-duracion 60
"""
import argparse
import json
import os
import sys
import time

from cortes import normalizar

MODELO_POR_DEFECTO = "gemini-2.5-flash"

PROMPT = """Eres un editor de video profesional. Mira el video completo (imagen y audio).

Objetivo de la edición: {objetivo}
{limite}
Devuelve SOLO los tramos que hay que CONSERVAR, en orden cronológico, sin solapes.
Cada tramo debe empezar y terminar en un punto natural (no cortes una palabra ni una frase a la mitad).
Usa timestamps en formato HH:MM:SS.mmm y en "motivo" explica en pocas palabras por qué se conserva."""

ESQUEMA = {
    "type": "object",
    "properties": {
        "cortes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "inicio": {"type": "string"},
                    "fin": {"type": "string"},
                    "motivo": {"type": "string"},
                },
                "required": ["inicio", "fin", "motivo"],
            },
        }
    },
    "required": ["cortes"],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-o", "--salida", default="cortes.json")
    ap.add_argument(
        "--objetivo",
        default="conservar los momentos más interesantes y eliminar silencios, errores y relleno",
    )
    ap.add_argument("--max-duracion", type=float, help="duración máxima del resultado, en segundos")
    ap.add_argument("--modelo", default=os.environ.get("GEMINI_MODEL", MODELO_POR_DEFECTO))
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"No existe el archivo: {args.video}")
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Falta GEMINI_API_KEY (créala en https://aistudio.google.com/apikey).")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit("Falta la librería: pip install -r requirements.txt")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    print(f"Subiendo {args.video} a Gemini...", file=sys.stderr)
    archivo = client.files.upload(file=args.video)
    while archivo.state.name == "PROCESSING":  # Gemini procesa el video antes de poder usarlo
        time.sleep(3)
        archivo = client.files.get(name=archivo.name)
    if archivo.state.name != "ACTIVE":
        sys.exit(f"Gemini no pudo procesar el video (estado: {archivo.state.name}).")

    limite = ""
    if args.max_duracion:
        limite = f"El resultado final no debe durar más de {args.max_duracion:g} segundos.\n"

    print(f"Analizando con {args.modelo}...", file=sys.stderr)
    resp = client.models.generate_content(
        model=args.modelo,
        contents=[archivo, PROMPT.format(objetivo=args.objetivo, limite=limite)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ESQUEMA,
            temperature=0.2,
        ),
    )

    try:
        datos = json.loads(resp.text)
        normalizar(datos["cortes"])  # valida formato de timestamps antes de guardar
    except (ValueError, KeyError, TypeError) as e:
        sys.exit(f"Gemini devolvió algo inesperado ({e}):\n{resp.text}")

    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"{len(datos['cortes'])} tramos guardados en {args.salida}", file=sys.stderr)

    try:
        client.files.delete(name=archivo.name)
    except Exception:
        pass  # el archivo expira solo a las 48 h


if __name__ == "__main__":
    main()
