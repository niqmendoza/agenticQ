"""Cierra un hallazgo mediante un retest trazable en otro build."""

import shutil
from uuid import uuid4

from audit import inspect
from release import case_digest
from session import WORK, append, load, run_id


def verify_fix(args):
    run, meta, events = load(args.run)
    other, fixed_meta, fixed_events = load(WORK / run_id(args.retest))
    base = inspect(run, meta, events)
    fixed = inspect(other, fixed_meta, fixed_events)
    finding = next((f for f in base["findings"] if f["id"] == args.finding), None)
    if (
        not finding
        or finding["id"] in base["invalid_findings"]
        or finding.get("fix_status") == "verified_fixed"
    ):
        raise ValueError("El hallazgo debe estar abierto y tener evidencia válida.")
    if (
        finding["confidence"] != "confirmed"
        or finding["classification"] != "product"
        or not finding["case_ids"]
    ):
        raise ValueError("El cierre requiere un defecto confirmado con casos.")
    if (
        meta["version"] == fixed_meta["version"]
        or meta["environment"] != fixed_meta["environment"]
    ):
        raise ValueError("Se necesita otro build en el mismo entorno.")
    p1, p2 = meta.get("provenance", {}), fixed_meta.get("provenance", {})
    if not p1.get("app") or p1["app"] != p2.get("app"):
        raise ValueError(
            "Se requieren dos ejecuciones de catálogo de la misma aplicación."
        )
    failed_time = max(
        (
            e["time_utc"]
            for key in finding["case_ids"]
            for _, e in base["attempts"][key]
            if e["status"] == "failed"
        ),
        default=None,
    )
    if not failed_time or fixed_meta["started_utc"] <= failed_time:
        raise ValueError("La corrida de retest debe ser posterior al fallo observado.")
    proofs = []
    for key in finding["case_ids"]:
        if (
            fixed["latest"].get(key) != "passed"
            or case_digest(base["cases"][key]) != case_digest(fixed["cases"][key])
            or p1["inputs"][key] != p2["inputs"].get(key)
        ):
            raise ValueError(
                f"{key}: falta un retest aprobado con los mismos criterios y fixtures."
            )
        attempt = fixed["attempts"][key][-1][1]
        refs = {result["evidence"] for result in attempt["results"]}
        for ref in sorted(refs):
            proofs.append((key, ref, fixed["evidence"][ref]))
    for key, ref, source in proofs:
        dest = f"evidencias/retest-{uuid4().hex}.md"
        shutil.copyfile(source, run / dest)
        append(
            run,
            {
                "kind": "note",
                "phase": "retest",
                "evidence": dest,
                "observation": f"{key} aprobado en {fixed_meta['version']} · {other.name}/{ref}",
            },
        )
    append(
        run,
        {
            "kind": "fix_verified",
            "finding_id": args.finding,
            "build": fixed_meta["version"],
            "retest": other.name,
            "evidence": dest,
        },
    )
    print(f"{args.finding} · verificado en {fixed_meta['version']}")
