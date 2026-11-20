"""Promueve las entradas declarativas de un plan V5 o V6 a un catálogo editable."""

import shutil
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import inspect
from regressions import application_suites, combine, load_batch, regression_root
from release import inside
from session import read_json, run_id, write_json, writer


def promote(args):
    source = Path(args.from_run).resolve()
    meta = read_json(source / "run.json")
    if meta.get("schema") not in ("qa-run/3", "qa-run/6"):
        raise ValueError("Formato de corrida desconocido.")
    plan = read_json(source / "plan.json")
    manifest = Path(args.manifest).resolve() if args.manifest else source / "suite.json"
    items = read_json(manifest)
    if not isinstance(items, list) or not items:
        raise ValueError("Indicá el manifiesto declarativo utilizado en la corrida.")
    by_id = {c["id"]: c for c in plan["cases"]}
    app = run_id(args.app)
    if args.regressions and not (args.case or args.manifest):
        raise ValueError("Indicá los casos aprobados con --case o --manifest.")
    if args.case:
        requested = set(args.case)
        if (
            len(requested) != len(args.case)
            or requested - {item["case"] for item in items}
        ):
            raise ValueError("--case debe identificar casos únicos del manifiesto.")
        items = [item for item in items if item["case"] in requested]
    keys = [item["case"] for item in items]
    if len(set(keys)) != len(keys) or set(keys) - by_id.keys():
        raise ValueError("Promové una selección única de casos del plan congelado.")
    root = regression_root(args.regressions) if args.regressions else None
    if root is not None:
        if meta["schema"] != "qa-run/6":
            raise ValueError("Repetí los casos en V6 para incorporarlos al repo de regresiones.")
        source_app = meta.get("provenance", {}).get("app")
        if source_app and source_app != app:
            raise ValueError(f"La corrida pertenece a {source_app}, no a {app}.")
        report = inspect(source, meta, read_json(source / "events.json"))
        pending = [key for key in keys if report["latest"].get(key) != "passed"]
        if pending:
            raise ValueError("Los casos requieren una aprobación con evidencia válida: " + ", ".join(pending))
        app_dir = root / app
        batches = app_dir / "lotes"
        if app_dir.is_symlink() or batches.is_symlink():
            raise ValueError("La carpeta de la aplicación y sus lotes deben estar en el repo.")
        target = batches / run_id(source.name)
    else:
        target = Path(args.out).resolve()
    lock = writer(Path(app)) if root is not None else nullcontext()
    with lock:
        save_batch(args, source, meta, plan, manifest, items, root, target)


def save_batch(args, source, meta, plan, manifest, items, root, target):
    by_id = {case["id"]: case for case in plan["cases"]}
    keys = [item["case"] for item in items]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or (target.exists() and root is None):
        raise ValueError("El catálogo de destino ya existe.")
    with TemporaryDirectory(dir=target.parent) as tmp:
        out = Path(tmp) / "catalogo"
        out.mkdir()
        (out / "fixtures").mkdir()
        cases = []
        for item in items:
            key = run_id(item["case"])
            case = {k: v for k, v in by_id[key].items() if k != "time_utc"}
            if item.get("body"):
                fixture = inside(manifest.parent, item["body"])
                name = f"fixtures/{key}.json"
                shutil.copyfile(fixture, out / name)
                item["body"] = name
            for step in case.get("browser_steps", []):
                if step["type"] == "upload":
                    file = inside(source / "fixtures", step["value"])
                    dest = (
                        out
                        / "fixtures"
                        / file.relative_to((source / "fixtures").resolve())
                    )
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(file, dest)
            cases.append(case)
        config = {
            "schema": "agentic-qc/suite-1",
            "app": args.app,
            "profile": "perfil.json",
            "cases": "casos.json",
            "manifest": "pasos.json",
        }
        requirements = plan.get("catalog")
        if root is not None and requirements:
            selected_requirements = {case["requirement"] for case in cases}
            requirements = [key for key in requirements if key in selected_requirements]
        if requirements:
            write_json(out / "requisitos.json", requirements)
            config["requirements"] = "requisitos.json"
        contract_paths = {
            meta.get("contracts", {}).get(key) for key in keys
        } - {None}
        if root is not None and len(contract_paths) > 1 and not args.openapi:
            raise ValueError("La selección usa varios contratos. Indicá un OpenAPI común.")
        contract_path = args.openapi or (
            next(iter(contract_paths)) if len(contract_paths) == 1 else None
        )
        if contract_path:
            contract = Path(contract_path)
            filename = f"openapi{contract.suffix}"
            shutil.copyfile(contract, out / filename)
            config["openapi"] = filename
        profile = read_json(args.profile) if args.profile else meta["profile"]
        for name, data in [
            ("casos", cases),
            ("pasos", items),
            ("perfil", profile),
            ("suite", config),
        ]:
            write_json(out / f"{name}.json", data)
        if root is not None:
            if target.exists():
                if snapshot(out) == snapshot(target):
                    print(f"{target / 'suite.json'} · Los casos ya están guardados.")
                    return
                raise ValueError("Esta corrida ya tiene un lote diferente en el catálogo.")
            existing = application_suites(root, args.app)
            corpus = args.corpus or meta.get("corpus")
            batch = load_batch(out / "suite.json", profile=args.profile, corpus=corpus)
            if any(
                saved["criteria"] != by_id[saved["id"]]["criteria"]
                for saved in batch.cases
            ):
                raise ValueError("El contrato cambió las comprobaciones del caso. Volvé a ejecutarlo antes de guardarlo.")
            combine(
                args.app,
                [
                    load_batch(path, profile=args.profile, corpus=corpus)
                    for path in existing
                ] + [batch],
            )
        out.rename(target)
    print(
        f"{target / 'suite.json'} · {len(keys)} casos. Fuera del manifiesto: {', '.join(sorted(by_id.keys() - set(keys))) or 'ninguno'}."
    )


def snapshot(path):
    return {
        file.relative_to(path): file.read_bytes()
        for file in path.rglob("*")
        if file.is_file()
    }
