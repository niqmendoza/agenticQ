"""Redactar secretos reconocibles manteniendo las líneas citables."""

import re

MASCARA = "[REDACTADO]"
BLOQUE = re.compile(
    r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----[\s\S]*?"
    r"-----END (?:[A-Z0-9]+ )*PRIVATE KEY-----"
)
TOKEN = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
    r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}|xox[bpas]-[A-Za-z0-9-]{15,}|"
    r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})\b"
)
CABECERA = re.compile(r"(?i)(\bauthorization[\"']?\s*[:=]\s*[\"']?(?:bearer|basic)\s+)[A-Za-z0-9./+_=-]{8,}")
ASIGNACION = re.compile(
    r"""(?im)(\b(?:[a-z0-9_]*[_-])?(?:password|passwd|contraseña|secret|client[_-]?secret|api[_-]?key|"""
    r"""access[_-]?token|refresh[_-]?token|dsn|authorization)[\"']?[ \t]*[:=][ \t]*)"""
    r"""("[^"\r\n]*"|'[^'\r\n]*'|[^\s,|;`<>\[\]{}]+)"""
)
MARCADOR = re.compile(
    r"(?i)^(?:true|false|null|none|str|string|changeme|example|ejemplo|placeholder|"
    r"dummy|redacted|redactado|\*+|x+|\$.*|[A-Z][A-Z0-9_]*(?:_PASSWORD|_SECRET|_TOKEN|_API_KEY|_DSN))$"
)


def sanear(texto):
    """Devuelve texto y cantidad. Es un detector heurístico, no un inventario DLP."""
    texto, bloques = BLOQUE.subn(
        lambda m: "\n".join(MASCARA for _ in m[0].split("\n")), texto
    )
    texto, tokens = TOKEN.subn(MASCARA, texto)
    texto, cabeceras = CABECERA.subn(lambda m: m[1] + MASCARA, texto)

    asignaciones = 0

    def sustituir(m):
        nonlocal asignaciones
        valor = m[2]
        literal = valor.strip("\"'")
        if not literal or literal == MASCARA or MARCADOR.fullmatch(literal):
            return m[0]
        if valor[0] not in "\"'" and m[1].endswith(" ") and len(literal) < 6:
            return m[0]
        asignaciones += 1
        if valor[0] in "\"'":
            return m[1] + valor[0] + MASCARA + valor[0]
        return m[1] + MASCARA

    return ASIGNACION.sub(sustituir, texto), bloques + tokens + cabeceras + asignaciones
