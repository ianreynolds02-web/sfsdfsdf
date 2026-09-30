# Edición de video con Gemini + ffmpeg

Gemini **mira** el video y decide los cortes. `ffmpeg` los **ejecuta**.

```
video.mp4 ──► analizar.py (Gemini) ──► cortes.json ──► aplicar_cortes.py (ffmpeg) ──► salida.mp4
```

## Requisitos
- `ffmpeg` y `ffprobe` en el PATH
- Python 3.10+ y `pip install -r requirements.txt`
- Una API key de Gemini (https://aistudio.google.com/apikey): `export GEMINI_API_KEY=...`

## Uso
```bash
./pipeline.sh video.mp4                                        # todo de una vez
./pipeline.sh clase.mp4 --objetivo "quitar silencios y muletillas"
./pipeline.sh largo.mp4 --max-duracion 60                      # resumen de máx. 60 s

# Revisar los cortes antes de aplicarlos (recomendado las primeras veces):
SOLO_ANALIZAR=1 ./pipeline.sh video.mp4
nano cortes.json
python3 aplicar_cortes.py video.mp4 --dry-run                  # ver los comandos
python3 aplicar_cortes.py video.mp4                            # generar salida.mp4
```

`cortes.json` es editable a mano; mira `ejemplo_cortes.json`. Los timestamps aceptan
segundos (`12.5`), `MM:SS` o `HH:MM:SS.mmm`. Los solapes se fusionan y lo que pase del
final del video se recorta solo.

## Notas
- Cada tramo se recodifica (`libx264`, `--crf 20`) para que el corte sea exacto al fotograma.
- Gemini puede equivocarse de unos segundos: por eso conviene revisar `cortes.json`.
- Modelo por defecto `gemini-2.5-flash`; cámbialo con `--modelo` o `GEMINI_MODEL`.

## Usar Claude / Codex en el mismo flujo
Los tres se comunican **por archivos**, no chateando entre ellos. Por ejemplo, tras
generar `cortes.json`, cualquiera puede ajustarlo o ampliar el script:
`claude -p "..."`, `codex exec "..."`, `gemini -p "..."`.
