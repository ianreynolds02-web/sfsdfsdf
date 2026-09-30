"""Utilidades compartidas: leer, validar y normalizar cortes.json."""
import json
import re

TS_RE = re.compile(r"^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$")


def parse_ts(valor):
    """Acepta segundos (12.5), "MM:SS", "HH:MM:SS" o "HH:MM:SS.ms" y devuelve segundos."""
    if isinstance(valor, (int, float)):
        return float(valor)
    valor = str(valor).strip()
    try:
        return float(valor)
    except ValueError:
        pass
    m = TS_RE.match(valor)
    if not m:
        raise ValueError(f"Timestamp inválido: {valor!r}")
    horas, minutos, segundos = m.groups()
    return int(horas or 0) * 3600 + int(minutos) * 60 + float(segundos)


def fmt_ts(segundos):
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def normalizar(cortes, duracion=None):
    """Devuelve [(inicio, fin, motivo)] ordenados, recortados a la duración y sin solapes."""
    tramos = []
    for c in cortes:
        ini, fin = parse_ts(c["inicio"]), parse_ts(c["fin"])
        if duracion is not None:
            ini, fin = max(0.0, ini), min(fin, duracion)
        if fin - ini < 0.1:  # descarta tramos vacíos o invertidos
            continue
        tramos.append([ini, fin, c.get("motivo", "")])
    tramos.sort(key=lambda t: t[0])

    fusionados = []
    for ini, fin, motivo in tramos:
        if fusionados and ini <= fusionados[-1][1]:  # solape: fusiona
            fusionados[-1][1] = max(fusionados[-1][1], fin)
        else:
            fusionados.append([ini, fin, motivo])
    return [tuple(t) for t in fusionados]


def cargar(ruta, duracion=None):
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    lista = datos["cortes"] if isinstance(datos, dict) else datos
    return normalizar(lista, duracion)
