"""Consultas de solo lectura sobre tablas o vistas declaradas en el perfil."""

import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class DatabaseUnavailable(Exception):
    pass


def identifier(value):
    return isinstance(value, str) and IDENTIFIER.fullmatch(value)


def validate_database(database):
    if not isinstance(database, dict) or database.get("driver") not in (
        "sqlite",
        "postgres",
    ):
        raise ValueError("database requiere driver sqlite o postgres.")
    if database["driver"] == "sqlite":
        path = database.get("path")
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError("SQLite requiere una ruta absoluta aprobada.")
    elif not identifier(database.get("dsn_env")):
        raise ValueError(
            "PostgreSQL requiere el nombre de una variable de entorno en dsn_env."
        )
    queries = database.get("queries")
    if not isinstance(queries, dict) or not queries:
        raise ValueError("Declará las consultas de lectura en database.queries.")
    for name, query in queries.items():
        if not identifier(name) or not isinstance(query, dict):
            raise ValueError("La consulta necesita un nombre y una definición.")
        table = query.get("table")
        if not isinstance(table, str) or not all(
            identifier(part) for part in table.split(".")
        ):
            raise ValueError("La consulta requiere una tabla o vista declarada.")
        for field in ("columns", "where", "order_by"):
            values = query.get(field, [])
            if not isinstance(values, list) or not all(
                identifier(value) for value in values
            ):
                raise ValueError(f"{field} debe contener nombres de columnas.")
            if len(values) != len(set(values)):
                raise ValueError(f"Hay nombres duplicados en {field}.")
        if not query.get("columns"):
            raise ValueError("La consulta requiere columnas explícitas.")


def query_arguments(profile, case):
    database = profile.get("database")
    if database is None:
        raise ValueError("El caso requiere una base de solo lectura en el perfil.")
    spec = case.get("db")
    if (
        not isinstance(spec, dict)
        or not identifier(spec.get("query"))
        or spec["query"] not in database["queries"]
    ):
        raise ValueError("El caso requiere db.query declarado en el perfil.")
    query = database["queries"][spec["query"]]
    parameters = spec.get("parameters", {})
    filters = query.get("where", [])
    if (
        not isinstance(parameters, dict)
        or set(parameters) != set(filters)
        or not all(
            type(value) in (str, int, float, bool) for value in parameters.values()
        )
    ):
        raise ValueError(
            "db.parameters debe contener los valores de los filtros declarados."
        )
    return database, query, [parameters[key] for key in filters]


def select_statement(query, placeholder):
    table = ".".join(f'"{part}"' for part in query["table"].split("."))
    columns = ", ".join(f'"{name}"' for name in query["columns"])
    filters = " AND ".join(
        f'"{name}" = {placeholder}' for name in query.get("where", [])
    )
    statement = f"SELECT {columns} FROM {table}"
    if filters:
        statement += f" WHERE {filters}"
    if query.get("order_by"):
        statement += " ORDER BY " + ", ".join(f'"{name}"' for name in query["order_by"])
    return statement + " LIMIT 101"


def read_rows(database, query, values):
    if database["driver"] == "sqlite":
        try:
            uri = Path(database["path"]).resolve().as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True, timeout=5)) as connection:
                return connection.execute(
                    select_statement(query, "?"), values
                ).fetchall()
        except (sqlite3.Error, OSError):
            raise DatabaseUnavailable(
                "No se completó la consulta de lectura a SQLite."
            ) from None

    dsn = os.environ.get(database["dsn_env"])
    if not dsn:
        raise DatabaseUnavailable("Falta la conexión PostgreSQL declarada.")
    try:
        import psycopg
    except ImportError:
        raise DatabaseUnavailable("Falta instalar el driver de PostgreSQL.") from None
    try:
        with psycopg.connect(dsn, connect_timeout=5) as connection:
            connection.read_only = True
            connection.execute("SET LOCAL statement_timeout = '5s'")
            return connection.execute(select_statement(query, "%s"), values).fetchall()
    except psycopg.Error:
        raise DatabaseUnavailable(
            "No se completó la consulta de lectura a PostgreSQL."
        ) from None
