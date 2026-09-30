#!/usr/bin/env python3
"""Paso 2: aplica cortes.json con ffmpeg y une los tramos en un solo video.

Uso:
    python3 aplicar_cortes.py video.mp4                 # genera salida.mp4
    python3 aplicar_cortes.py video.mp4 --dry-run       # solo muestra los comandos
    python3 aplicar_cortes.py video.mp4 -c mis_cortes.json -o final.mp4
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

from cortes import cargar, fmt_ts


def duracion_video(ruta):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", ruta],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-c", "--cortes", default="cortes.json")
    ap.add_argument("-o", "--salida", default="salida.mp4")
    ap.add_argument("--crf", type=int, default=20, help="calidad x264 (menor = mejor, 18-23 típico)")
    ap.add_argument("--dry-run", action="store_true", help="muestra los comandos sin ejecutarlos")
    args = ap.parse_args()

    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("Falta ffmpeg/ffprobe en el PATH.")
    if not os.path.isfile(args.video):
        sys.exit(f"No existe el archivo: {args.video}")

    dur = duracion_video(args.video)
    tramos = cargar(args.cortes, duracion=dur)
    if not tramos:
        sys.exit("cortes.json no tiene tramos válidos.")

    total = sum(fin - ini for ini, fin, _ in tramos)
    print(f"{len(tramos)} tramos: {fmt_ts(total)} de {fmt_ts(dur)} originales", file=sys.stderr)

    tmp = tempfile.mkdtemp(prefix="cortes_")
    lista = os.path.join(tmp, "lista.txt")
    comandos = []
    try:
        with open(lista, "w", encoding="utf-8") as f:
            for i, (ini, fin, motivo) in enumerate(tramos):
                pedazo = os.path.join(tmp, f"tramo_{i:03d}.mp4")
                # -ss después de -i = corte exacto al fotograma; se recodifica cada tramo
                comandos.append([
                    "ffmpeg", "-y", "-loglevel", "error", "-i", args.video,
                    "-ss", f"{ini:.3f}", "-to", f"{fin:.3f}",
                    "-c:v", "libx264", "-crf", str(args.crf), "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k", pedazo,
                ])
                f.write(f"file '{pedazo}'\n")
                print(f"  {i + 1:>2}. {fmt_ts(ini)} -> {fmt_ts(fin)}  {motivo}", file=sys.stderr)
        comandos.append([
            "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
            "-i", lista, "-c", "copy", args.salida,
        ])

        for cmd in comandos:
            if args.dry_run:
                print(shlex.join(cmd))
            else:
                subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if not args.dry_run:
        print(f"Listo: {args.salida}", file=sys.stderr)


if __name__ == "__main__":
    main()
