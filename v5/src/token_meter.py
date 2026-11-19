"""Importa los contadores nativos de una conversación aislada de QA."""

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from contracts import observed_time
from markdown import inline, table, write_markdown
from session import append, load, read_json, write_json

STAGES = {
    "preparacion": "Preparación",
    "analisis": "Lectura y análisis",
    "diseno": "Diseño de casos",
    "ejecucion": "Ejecución",
    "cierre": "Cierre",
    "mixta": "Mixta",
}
SOURCES = {
    "otel": "OpenTelemetry · spans chat",
    "native": "Exportación nativa por llamada",
}


class TokensUnavailable(ValueError):
    pass


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                if not line.endswith("\n"):
                    # El exportador puede estar terminando de escribir la última línea.
                    break
                raise TokensUnavailable(
                    f"La fuente contiene JSON inválido en la línea {number}."
                ) from None
            if not isinstance(row, dict):
                raise TokensUnavailable(
                    f"La línea {number} de la fuente no contiene un registro."
                )
            yield row


def text_field(value):
    return value if isinstance(value, str) and value else None


def otel_time(value):
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(type(part) is int for part in value)
    ):
        seconds, nanos = value
        if 0 <= nanos < 1_000_000_000:
            return datetime.fromtimestamp(seconds, tz=timezone.utc) + timedelta(
                microseconds=nanos // 1_000
            )
    return observed_time(value)


def otel_rows(rows):
    spans = []
    roots = defaultdict(set)
    for row in rows:
        attributes = row.get("attributes")
        if not isinstance(attributes, dict):
            continue
        context = row.get("spanContext")
        context = context if isinstance(context, dict) else {}
        trace = text_field(row.get("traceId") or context.get("traceId"))
        span = text_field(row.get("spanId") or context.get("spanId"))
        session = text_field(attributes.get("gen_ai.conversation.id"))
        operation = attributes.get("gen_ai.operation.name")
        parent = row.get("parentSpanId") or row.get("parentSpanContext")
        if operation == "invoke_agent" and session and trace and not parent:
            roots[trace].add(session)
        if operation == "chat":
            spans.append(
                (
                    trace,
                    span,
                    session,
                    row.get("startTime"),
                    row.get("endTime"),
                    attributes.get("gen_ai.usage.input_tokens"),
                    attributes.get("gen_ai.usage.output_tokens"),
                )
            )

    for trace, span, session, start, end, inputs, outputs in spans:
        assigned = roots.get(trace, set())
        if len(assigned) == 1:
            session = next(iter(assigned))
        if not session:
            continue
        yield {
            "scope": session,
            "id": f"{trace}/{span}" if trace and span else None,
            "start": start,
            "end": end,
            "input": inputs,
            "output": outputs,
        }


def native_rows(rows):
    for row in rows:
        if text_field(row.get("scope")):
            yield {
                key: row.get(key)
                for key in ("scope", "id", "start", "end", "input", "output")
            }


def select_usage(path, format_name, scope=None):
    if not path.is_file():
        raise TokensUnavailable("Falta el archivo de contadores nativos.")
    reader = otel_rows if format_name == "otel" else native_rows
    rows = list(reader(read_rows(path)))
    scopes = {row["scope"] for row in rows}
    if not scopes:
        raise TokensUnavailable(
            "El archivo no contiene llamadas de una conversación identificable."
        )
    if scope is None:
        if len(scopes) != 1:
            raise TokensUnavailable(
                "No se pudo aislar una conversación. Indicá --scope de un registro con consumo nativo."
            )
        scope = next(iter(scopes))
    if scope not in scopes:
        raise TokensUnavailable(
            "La conversación indicada todavía no tiene llamadas exportadas."
        )
    calls = {}
    for row in rows:
        if row["scope"] != scope:
            continue
        identifier = text_field(row["id"])
        try:
            start = otel_time(row["start"])
            end = otel_time(row["end"])
        except (ValueError, OverflowError, OSError, TypeError):
            raise TokensUnavailable(
                "Una llamada de la conversación tiene un intervalo inválido."
            ) from None
        if not identifier or end < start:
            raise TokensUnavailable(
                "Una llamada carece de identificador único o intervalo válido."
            )
        counts = tuple(
            value if type(value) is int and value >= 0 else None
            for value in (row["input"], row["output"])
        )
        call = (start, end, *counts)
        if identifier in calls and calls[identifier] != call:
            raise TokensUnavailable(
                "La fuente tiene registros contradictorios para una misma llamada."
            )
        calls[identifier] = call
    return scope, calls


def usage_config(run):
    path = run / "tokens.json"
    return read_json(path) if path.is_file() else None


def require_usage_ready(run, meta, *, verify=False):
    if not meta.get("tokens_required"):
        return
    config = usage_config(run)
    if not config or not Path(config["file"]).is_file():
        raise TokensUnavailable(
            "No hay una fuente de tokens verificada. Ejecutá tokens-check y avisá al usuario si el contador no está disponible."
        )

    if verify:
        try:
            _, calls = select_usage(
                Path(config["file"]), config["format"], config["scope"]
            )
        except OSError:
            raise TokensUnavailable(
                "No se pudo leer la fuente de tokens nativos."
            ) from None
        if any(None in call[2:] for call in calls.values()):
            raise TokensUnavailable("Hay llamadas sin contador de entrada o salida.")
        if set(config["baseline"]) - calls.keys():
            raise TokensUnavailable(
                "El archivo ya no contiene las llamadas de la comprobación inicial."
            )


def check_tokens(args):
    run, _, _ = load(args.run)
    file = Path(args.file).resolve()
    config = usage_config(run)
    if config:
        if (
            str(file) != config["file"]
            or args.format != config["format"]
            or args.scope
            and args.scope != config["scope"]
        ):
            raise ValueError("La corrida ya tiene una fuente y conversación asignadas.")
    try:
        scope, calls = select_usage(
            file, args.format, config["scope"] if config else args.scope
        )
        complete = [count for _, _, *count in calls.values() if None not in count]
        if len(complete) != len(calls):
            raise TokensUnavailable("Hay llamadas sin contador de entrada o salida.")
        if not any(sum(count) for count in complete):
            raise TokensUnavailable(
                "No se observan contadores de entrada y salida medibles."
            )
    except (OSError, TokensUnavailable) as error:
        print(f"Medición de tokens bloqueada · {error}", file=sys.stderr)
        return 3
    if config is None:
        write_json(
            run / "tokens.json",
            {
                "file": str(file),
                "format": args.format,
                "scope": scope,
                "baseline": sorted(calls),
            },
        )
        append(
            run,
            {
                "kind": "note",
                "phase": "medicion",
                "observation": f"Fuente nativa comprobada en una conversación · {SOURCES[args.format]}.",
            },
        )
    print(f"Tokens listos. Llamadas con entrada y salida · {len(complete)}.")
    return 0


def mark_stage(args):
    run, meta, _ = load(args.run)
    require_usage_ready(run, meta)
    append(
        run,
        {
            "kind": "note",
            "phase": "medicion",
            "observation": f"Inicio de etapa · {STAGES[args.stage]}.",
            "token_stage": args.stage,
        },
    )


def token_report(run, meta, events):
    config = usage_config(run)
    if not config:
        if not meta.get("tokens_required"):
            return None
        return {
            "blocked": True,
            "reason": "Falta verificar una fuente de tokens nativos.",
        }
    try:
        _, calls = select_usage(Path(config["file"]), config["format"], config["scope"])
    except (OSError, TokensUnavailable) as error:
        return {"blocked": True, "reason": str(error)}
    baseline = set(config["baseline"])
    boundaries = [
        (observed_time(event["time_utc"]), event["token_stage"])
        for event in events
        if "token_stage" in event
    ]
    entries = []
    totals = defaultdict(lambda: [0, 0, 0])
    incomplete = 0
    for identifier, (start, end, input_count, output_count) in sorted(
        calls.items(), key=lambda item: item[1][0]
    ):
        stage = "preparacion"
        for boundary, label in boundaries:
            if boundary <= start:
                stage = label
            elif boundary < end:
                stage = "mixta"
                break
            else:
                break
        if input_count is None or output_count is None:
            incomplete += 1
        else:
            totals[stage][0] += 1
            totals[stage][1] += input_count
            totals[stage][2] += output_count
        entries.append(
            (
                hashlib.sha256(identifier.encode()).hexdigest()[:16],
                STAGES[stage],
                start.isoformat(),
                end.isoformat(),
                input_count,
                output_count,
            )
        )
    latest = max(call[1] for call in calls.values())
    tested = [
        observed_time(event["finished_at"])
        for event in events
        if event["kind"] == "execution" and event.get("finished_at")
    ]
    reason = ""
    if baseline - calls.keys():
        reason = "La fuente perdió llamadas que aparecían en la comprobación inicial."
    elif incomplete:
        reason = f"Hay {incomplete} llamada(s) sin contador completo."
    elif not calls.keys() - baseline:
        reason = (
            "Todavía no se exportaron llamadas posteriores a la comprobación inicial."
        )
    elif tested and latest < max(tested):
        reason = "La última llamada exportada es anterior al último intento registrado."
    return {
        "blocked": bool(reason),
        "reason": reason,
        "source": SOURCES[config["format"]],
        "totals": totals,
        "entries": entries,
        "latest": latest.isoformat(),
    }


def token_lines(report):
    lines = ["## Consumo nativo del agente", ""]
    if report is None:
        return lines + [
            "La sesión histórica carece de una medición nativa vinculada.",
            "",
        ]
    if report["reason"]:
        lines += [f"- Estado · {inline(report['reason'])}", ""]
    if "entries" not in report:
        return lines
    totals = report["totals"]
    input_count = sum(row[1] for row in totals.values())
    output_count = sum(row[2] for row in totals.values())
    total_label = "Subtotal observado" if report["blocked"] else "Total observado"
    lines += [
        f"- Fuente · {report['source']}",
        f"- Última llamada exportada · {report['latest']}",
        f"- Tokens de entrada observados · {input_count}",
        f"- Tokens de salida observados · {output_count}",
        f"- {total_label} · {input_count + output_count}",
        "- Alcance · llamadas exportadas de la conversación asignada hasta el corte. Las llamadas posteriores al corte pertenecen a una revisión posterior.",
        "",
        *table(
            ("Etapa", "Llamadas con contador", "Entrada", "Salida", "Total"),
            (
                (label, *totals[key], sum(totals[key][1:]))
                if key in totals
                else (label, "—", "—", "—", "—")
                for key, label in STAGES.items()
            ),
        ),
    ]
    return lines


def write_token_evidence(path, report):
    write_markdown(
        path,
        [
            "# Llamadas medidas del agente",
            "",
            *token_lines(report),
            *table(
                (
                    "Llamada (hash)",
                    "Etapa",
                    "Inicio UTC",
                    "Fin UTC",
                    "Entrada",
                    "Salida",
                ),
                (
                    (key, label, start, end, inline(inputs), inline(outputs))
                    for key, label, start, end, inputs, outputs in report["entries"]
                ),
            ),
        ],
    )
