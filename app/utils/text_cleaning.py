"""Funciones de normalización y limpieza de texto (usadas por MDM y RAG)."""

from __future__ import annotations

import json
import re
import unicodedata

_WS_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")


def strip_accents(text: str) -> str:
    """Elimina acentos/diacríticos (Perú -> Peru)."""
    if not isinstance(text, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    """Normaliza para comparaciones: minúsculas, sin acentos, sin signos, espacios colapsados."""
    if text is None:
        return ""
    text = strip_accents(str(text)).lower().strip()
    text = _NON_ALNUM_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def normalize_email(email: str) -> str:
    """Normaliza correos para comparación (minúsculas, sin espacios)."""
    if not isinstance(email, str):
        return ""
    return email.strip().lower()


def normalize_country(value: str) -> str:
    """Mapea variantes de país a una forma canónica (Perú/Peru/PE -> Peru)."""
    if value is None:
        return ""
    key = normalize_text(value)
    mapping = {
        "peru": "Peru",
        "pe": "Peru",
        "per": "Peru",
        "chile": "Chile",
        "cl": "Chile",
        "colombia": "Colombia",
        "co": "Colombia",
        "ecuador": "Ecuador",
        "ec": "Ecuador",
        "bolivia": "Bolivia",
        "bo": "Bolivia",
        "argentina": "Argentina",
        "ar": "Argentina",
        "mexico": "Mexico",
        "mx": "Mexico",
    }
    return mapping.get(key, value.strip())


def extract_json(raw: str) -> dict | list | None:
    """Extrae el primer objeto/array JSON de un texto (salida típica de un LLM)."""
    if not raw:
        return None
    raw = raw.strip()
    # Quitar fences de markdown ```json ... ```
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Buscar el primer bloque { ... } o [ ... ] balanceado
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == opener:
                depth += 1
            elif raw[i] == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start : i + 1])
                    except json.JSONDecodeError:
                        break
    return None
