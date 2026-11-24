"""Carga las pruebas versionadas de una aplicación y las de la release actual."""

from pathlib import Path
from types import SimpleNamespace

from release import LoadedSuite, digest, load_suite
from session import run_id


def regression_root(path):
    return Path(path or "regresiones").resolve()


def application_suites(root, app):
    legacy = root / app / "suite.json"
    batches = sorted((root / app / "lotes").glob("*/suite.json"))
    return ([legacy] if legacy.is_file() else []) + batches


def load_batch(suite_file, *, profile=None, corpus=None, chrome_visible=False):
    return load_suite(
        SimpleNamespace(
            suite=suite_file,
            profile=profile,
            corpus=corpus,
            chrome_visible=chrome_visible,
        )
    )


def load_application(args):
    app = run_id(args.app)
    paths = application_suites(regression_root(args.regressions), app)
    saved_count = len(paths)
    if args.new_suite:
        paths.append(Path(args.new_suite).resolve())
    if not paths:
        raise ValueError(
            f"No hay regresiones guardadas para {app}. Indicá la primera suite con --new-suite."
        )
    batches = [
        load_batch(
            path, profile=args.profile, corpus=args.corpus,
            chrome_visible=args.chrome_visible,
        )
        for path in paths
    ]
    combined, case_batches = combine(app, batches)
    combined.provenance["regressions"] = {
        "saved": [key for key, index in case_batches.items() if index < saved_count],
        "new": [key for key, index in case_batches.items() if index >= saved_count],
    }
    return combined, case_batches


def combine(app, batches):
    first = batches[0]
    requirements = []
    cases, manifest = [], []
    case_batches = {}
    bodies, uploads = {}, {}
    definitions, inputs, sources = {}, {}, {}
    contracts = {}
    contract_hashes = []
    for index, batch in enumerate(batches):
        info = batch.provenance
        if info["app"] != app:
            raise ValueError(f"El catálogo de {info['app']} no pertenece a {app}.")
        if batch.profile != first.profile:
            raise ValueError("Los catálogos usan perfiles distintos. Indicá un perfil común con --profile.")
        if batch.corpus != first.corpus:
            raise ValueError("Los catálogos usan fuentes distintas. Indicá un segundo cerebro común con --corpus.")
        for case in batch.cases:
            key = case["id"]
            if key in case_batches:
                raise ValueError(f"El caso {key} ya está en el catálogo. Revisá su ID antes de incorporarlo.")
            case_batches[key] = index
        for name, data in batch.uploads.items():
            if name in uploads and uploads[name] != data:
                raise ValueError(f"El archivo de prueba {name} tiene contenidos distintos entre catálogos.")
            uploads[name] = data
        cases.extend(batch.cases)
        manifest.extend(batch.manifest)
        bodies.update(batch.bodies)
        requirements.extend(batch.requirements or [])
        definitions.update(info["cases"])
        inputs.update(info["inputs"])
        sources.update(info["sources"])
        contracts.update(batch.contracts)
        if info["contract"] and info["contract"] not in contract_hashes:
            contract_hashes.append(info["contract"])
    requirements = list(dict.fromkeys(requirements)) or None
    provenance = {
        **first.provenance,
        "suite": digest([list(inputs.items()), requirements, sources]),
        "cases": definitions,
        "inputs": inputs,
        "sources": sources,
        "contract": digest(contract_hashes) if len(contract_hashes) > 1
        else contract_hashes[0] if contract_hashes else None,
    }
    return LoadedSuite(
        first.profile, first.corpus, cases, manifest, bodies, uploads, requirements,
        provenance, contracts,
    ), case_batches
