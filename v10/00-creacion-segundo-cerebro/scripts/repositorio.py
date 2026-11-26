"""Inventario reproducible y lectura local de objetos Git, sin ejecutar código del proyecto."""

import hashlib
import re
import subprocess
from collections import Counter
from contextlib import contextmanager
from pathlib import PurePosixPath

from higiene import sanear

SCHEMA = "agentic-qc/cerebro-1"
IGNORADOS = {
    ".git", ".venv", "venv", "node_modules", "vendor", "dist", "build", "target",
    "coverage", ".next", ".cache", "__pycache__", "obj", "bin",
}
LOCKS = {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "go.sum", "cargo.lock"}
EXTENSIONES = set(
    ".py .js .jsx .ts .tsx .mjs .cjs .vue .svelte .html .css .scss .java .kt .scala "
    ".cs .fs .vb .go .rs .php .rb .swift .m .c .cpp .h .hpp .sql .graphql .gql "
    ".proto .sh .ps1 .md .markdown .rst .adoc .txt .ini .toml .json .yml .yaml .xml "
    ".gradle .kts .csproj .sln .properties .tf .ex .exs .dart .lua .pl .r .feature".split()
)
ESPECIALES = {"dockerfile", "makefile", "gemfile", "rakefile", "jenkinsfile"}
ID = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
DECLARACION = re.compile(
    r"^\s*(?:(?:public|private|internal|protected|static|export|default|async|abstract|final|pub|override)\s+)*"
    r"(?:class|struct|interface|enum|type|trait|def|func|function|fn|record)\s+([\w.]+)"
)


def git(repo, *args):
    try:
        output = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, check=True,
        )
    except FileNotFoundError as error:
        raise ValueError("Instalá Git en el entorno de la etapa 00.") from error
    except subprocess.CalledProcessError as error:
        raise ValueError("Git no pudo leer el repositorio o la revisión local indicada.") from error
    return output.stdout


def snapshot(repo, rev):
    commit = git(repo, "rev-parse", "--verify", "--end-of-options", f"{rev}^{{commit}}").decode("ascii").strip()
    return commit, git(repo, "ls-tree", "-r", "-l", "-z", "--full-tree", commit)


@contextmanager
def objetos(repo):
    with subprocess.Popen(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    ) as child:
        def leer(oid, size):
            child.stdin.write(oid + b"\n")
            child.stdin.flush()
            header = child.stdout.readline().split()
            if header != [oid, b"blob", str(size).encode("ascii")]:
                raise ValueError("Git devolvió un objeto distinto del inventariado.")
            data = child.stdout.read(size)
            if len(data) != size or child.stdout.read(1) != b"\n":
                raise ValueError("Git devolvió un objeto incompleto.")
            return data
        try:
            yield leer
        finally:
            child.stdin.close()
            child.wait()


def descarte(path, mode, kind, size, limite):
    nombre = path.name.casefold()
    if kind != b"blob" or mode not in {b"100644", b"100755"}:
        return "submodulo_o_enlace"
    if any(piece.casefold() in IGNORADOS for piece in path.parts[:-1]):
        return "dependencia_o_generado"
    if (
        nombre == ".env" or nombre.startswith(".env.") or
        re.search(r"(?:credencial|credentials|secrets?|id_rsa|id_ed25519)", nombre)
        or path.parts[0].casefold() in {".ssh", ".aws"}
    ):
        return "archivo_sensible"
    if nombre in LOCKS or nombre.endswith((".min.js", ".min.css", ".map", ".g.cs")):
        return "dependencia_o_generado"
    if path.suffix.casefold() not in EXTENSIONES and not any(
        nombre == special or nombre.startswith(special + ".") for special in ESPECIALES
    ):
        return "formato_excluido"
    if size > limite:
        return "archivo_grande"
    return None


def inventario(tree, limite):
    omisiones = Counter()
    files, huellas = [], []
    for row in tree.split(b"\0"):
        if not row:
            continue
        raw, name = row.split(b"\t", 1)
        mode, kind, oid, size = raw.split()
        try:
            path = PurePosixPath(name.decode("utf-8"))
        except UnicodeDecodeError:
            omisiones["ruta_no_utf8"] += 1
            continue
        if any(ord(char) < 32 for char in path.as_posix()):
            omisiones["ruta_con_controles"] += 1
            continue
        huellas.append((path, mode.decode("ascii"), oid.decode("ascii")))
        nbytes = int(size) if size != b"-" else 0
        if reason := descarte(path, mode, kind, nbytes, limite):
            omisiones[reason] += 1
        else:
            files.append((path, oid, nbytes))
    return files, omisiones, huellas


def configurar(raw):
    if not isinstance(raw, dict):
        raise ValueError("La configuración de módulos debe ser un objeto.")
    modulos, prefijos = {}, {}
    for id_, config in raw.items():
        if not ID.fullmatch(id_) or id_ == "raiz" or not isinstance(config, dict):
            raise ValueError("Usá IDs de módulos en minúsculas y guiones. raiz se asigna automáticamente.")
        paths = config.get("prefijos")
        deps = config.get("depende_de", [])
        if (
            set(config) - {"prefijos", "depende_de"}
            or not isinstance(paths, list) or not paths
            or not isinstance(deps, list) or any(dep not in raw or dep == id_ for dep in deps)
        ):
            raise ValueError(f"Configuración inválida para el módulo {id_}.")
        for value in paths:
            if not isinstance(value, str):
                raise ValueError("Los prefijos son rutas relativas del repositorio.")
            path = PurePosixPath(value)
            if path.is_absolute() or not path.parts or ".." in path.parts or path in prefijos:
                raise ValueError("Cada prefijo relativo debe ser único.")
            prefijos[path] = id_
        modulos[id_] = sorted(set(deps))
    return modulos, dict(sorted(prefijos.items(), key=lambda item: len(item[0].parts), reverse=True))


def modulo(path, prefijos, reservados):
    for prefix, id_ in prefijos.items():
        if path == prefix or prefix in path.parents:
            return id_
    if len(path.parts) == 1:
        return "raiz"
    top = path.parts[0]
    if ID.fullmatch(top) and top not in reservados and top != "raiz":
        return top
    return "dir-" + hashlib.sha256(top.encode()).hexdigest()[:20]


def perfil_archivo(path, texto):
    """Etiquetas orientativas. Las afirmaciones se validan contra rangos aparte."""
    nombre = path.name.casefold()
    parts = {part.casefold() for part in path.parts}
    if path.suffix.casefold() in {".md", ".rst", ".adoc", ".txt", ".markdown"}:
        tipo = "documentacion"
    elif "test" in nombre or parts & {"tests", "spec", "specs", "__tests__"} or nombre.endswith(".feature"):
        tipo = "pruebas"
    elif nombre.startswith(("openapi", "swagger")) or path.suffix.casefold() in {".graphql", ".gql", ".proto"}:
        tipo = "contrato"
    elif path.suffix.casefold() == ".sql" or parts & {"migrations", "schemas", "models"}:
        tipo = "datos"
    elif path.suffix.casefold() in {".yaml", ".yml", ".toml", ".ini", ".tf", ".properties"} or nombre in ESPECIALES:
        tipo = "configuracion"
    else:
        tipo = "fuente"
    simbolos = []
    for numero, linea in enumerate(texto.splitlines(), 1):
        if match := DECLARACION.match(linea):
            simbolos.append([match[1], numero])
            if len(simbolos) == 12:
                break
    return tipo, simbolos


def texto_seguro(blob):
    if b"\0" in blob:
        raise ValueError("archivo_binario")
    try:
        text = blob.decode("utf-8-sig")
    except UnicodeError as error:
        raise ValueError("texto_no_utf8") from error
    normal = text.replace("\r\n", "\n").removesuffix("\n")
    return sanear(normal)
