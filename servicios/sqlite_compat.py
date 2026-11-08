import os
import sqlite3
from datetime import datetime
from decimal import Decimal


def es_sqlite(cadena_conexion: str) -> bool:
    return (
        cadena_conexion.startswith("sqlite")
        or cadena_conexion.startswith("file:")
        or cadena_conexion.endswith(".db")
        or cadena_conexion.endswith(".sqlite")
        or cadena_conexion.endswith(".sqlite3")
    )


def ruta_sqlite(cadena_conexion: str) -> str:
    if cadena_conexion.startswith("sqlite:///"):
        return cadena_conexion.removeprefix("sqlite:///")
    if cadena_conexion.startswith("sqlite://"):
        return cadena_conexion.removeprefix("sqlite://")
    if cadena_conexion.startswith("file:///"):
        return cadena_conexion.removeprefix("file:///")
    if cadena_conexion.startswith("file://"):
        return cadena_conexion.removeprefix("file://")
    return cadena_conexion


def abrir_conexion(cadena_conexion: str):
    if not es_sqlite(cadena_conexion):
        raise ValueError("La cadena no es SQLite")

    ruta = ruta_sqlite(cadena_conexion)
    directorio = os.path.dirname(ruta)
    if directorio:
        os.makedirs(directorio, exist_ok=True)

    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def decimal_a_bd(valor: Decimal | float | int) -> float:
    return float(valor)


def datetime_a_bd(valor: datetime | str | None) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor
    return valor.isoformat(timespec="microseconds")


def decimal_desde_bd(valor) -> Decimal:
    return Decimal(str(valor))


def datetime_desde_bd(valor) -> datetime | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))
