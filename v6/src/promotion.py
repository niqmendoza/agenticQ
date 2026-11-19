"""Promueve las entradas declarativas de un plan V5 o V6 a un catálogo editable."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from release import inside
from session import read_json, run_id, write_json


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
    keys = [item["case"] for item in items]
    if len(set(keys)) != len(keys) or set(keys) - by_id.keys():
        raise ValueError("Promové una selección única de casos del plan congelado.")
    target = Path(args.out).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
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
            "app": run_id(args.app),
            "profile": "perfil.json",
            "cases": "casos.json",
            "manifest": "pasos.json",
        }
        if plan.get("catalog"):
            write_json(out / "requisitos.json", plan["catalog"])
            config["requirements"] = "requisitos.json"
        for name, data in [
            ("casos", cases),
            ("pasos", items),
            ("perfil", meta["profile"]),
            ("suite", config),
        ]:
            write_json(out / f"{name}.json", data)
        out.rename(target)
    print(
        f"{target / 'suite.json'} · {len(keys)} casos. Fuera del manifiesto: {', '.join(sorted(by_id.keys() - set(keys))) or 'ninguno'}."
    )
