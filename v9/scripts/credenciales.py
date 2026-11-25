"""Entregar al runner solo las variables declaradas por la suite."""

import os
import re
import stat

from rutas import V9

ARCHIVO_CREDENCIALES = V9 / "credenciales.txt"
NOMBRE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
LIMITE = 64 * 1024
RESERVADAS = {"PATH", "HOME", "ENV", "BASH_ENV", "QC_WORKSPACE"}
PREFIJOS_RESERVADOS = ("PYTHON", "LD_", "DYLD_")


def referencias(caso, paso, perfil):
    canal = paso["via"]
    if canal == "playwright":
        return {accion["value_env"] for accion in caso.get("browser_steps", []) if "value_env" in accion}
    if canal in ("http", "api"):
        nombre = perfil.get("credentials", {}).get(caso["http"].get("actor", "anonymous"))
    else:
        nombre = perfil.get("database", {}).get("dsn_env")
    return {nombre} if nombre else set()


def entorno_para(nombres, archivo):
    """Aceptar texto literal. Las variables ya inyectadas en el runner tienen prioridad."""
    if any(
        not NOMBRE.fullmatch(nombre)
        or nombre in RESERVADAS
        or nombre.startswith(PREFIJOS_RESERVADOS)
        for nombre in nombres
    ):
        raise ValueError("El perfil contiene un nombre de variable inválido.")
    entorno = dict(os.environ)
    requeridas = {nombre for nombre in nombres if not entorno.get(nombre)}
    if not requeridas or not archivo.exists():
        return entorno
    if archivo.is_symlink() or not archivo.is_file():
        raise ValueError("Credenciales requieren un archivo local regular.")
    with archivo.open("rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > LIMITE:
            raise ValueError("El archivo de credenciales debe ser regular y pesar hasta 64 KiB.")
        try:
            texto = stream.read(LIMITE + 1).decode("utf-8-sig")
        except UnicodeError:
            raise ValueError("El archivo de credenciales debe estar en UTF-8.") from None
    vistos = set()
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        alias, separador, valor = linea.partition("=")
        alias = alias.strip()
        if not separador or not NOMBRE.fullmatch(alias) or alias in vistos or "\x00" in valor:
            raise ValueError(f"Credenciales: par NOMBRE=valor inválido o duplicado en línea {numero}.")
        vistos.add(alias)
        if valor and os.name == "posix" and info.st_mode & 0o077:
            raise ValueError("El archivo de credenciales requiere permisos privados (chmod 600).")
        if alias in requeridas and valor:
            entorno[alias] = valor
    return entorno


def ocultar(texto, secretos):
    for valor in sorted({valor for valor in secretos if valor}, key=len, reverse=True):
        texto = texto.replace(valor, "[REDACTADO]")
    return texto
