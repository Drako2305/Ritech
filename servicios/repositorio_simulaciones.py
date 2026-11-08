"""Persistencia de simulaciones.

Interfaz + implementación PostgreSQL, siguiendo el mismo patrón que
GeneradorVariacionNasdaq: MotorSimulacion/la API no dependen de psycopg,
solo de este contrato, así que en los tests se puede usar un repositorio
falso sin tocar una base de datos real.
"""

from abc import ABC, abstractmethod
import sqlite3
from datetime import datetime
from decimal import Decimal

import psycopg
from psycopg import errors as errores_psycopg
from psycopg.rows import dict_row

from dominio.excepciones import IdentificadorInvalidoError, UsuarioNoEncontradoError
from dominio.simulacion import Simulacion
from servicios.sqlite_compat import abrir_conexion, decimal_a_bd, decimal_desde_bd, datetime_a_bd, datetime_desde_bd, es_sqlite


class RepositorioSimulaciones(ABC):
    """Contrato: cualquier forma de guardar/consultar simulaciones debe cumplirlo."""

    @abstractmethod
    def guardar(self, simulacion: Simulacion) -> None:
        raise NotImplementedError

    @abstractmethod
    def listar_por_usuario(self, id_usuario: str) -> list[Simulacion]:
        raise NotImplementedError


class RepositorioSimulacionesPostgres(RepositorioSimulaciones):
    """Guarda cada simulación en la tabla `simulaciones` (ver db/schema.sql)."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion

    def guardar(self, simulacion: Simulacion) -> None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    CREATE TABLE IF NOT EXISTS simulaciones (
                        id TEXT PRIMARY KEY,
                        id_usuario TEXT NOT NULL,
                        capital_inicial REAL NOT NULL,
                        variacion_nasdaq REAL NOT NULL,
                        rendimiento_porcentaje REAL NOT NULL,
                        monto_final REAL NOT NULL,
                        fecha_simulacion TEXT NOT NULL,
                        FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
                    )
                    """
                )
                try:
                    conexion.execute(
                        "INSERT INTO simulaciones (id, id_usuario, capital_inicial, variacion_nasdaq, rendimiento_porcentaje, monto_final, fecha_simulacion) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            simulacion.id_simulacion,
                            simulacion.id_usuario,
                            decimal_a_bd(simulacion.capital_inicial),
                            decimal_a_bd(simulacion.variacion_nasdaq),
                            decimal_a_bd(simulacion.rendimiento_porcentaje),
                            decimal_a_bd(simulacion.monto_final),
                            datetime_a_bd(simulacion.fecha_simulacion),
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    raise UsuarioNoEncontradoError(simulacion.id_usuario) from error
            return

        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    INSERT INTO simulaciones
                        (id, id_usuario, capital_inicial, variacion_nasdaq,
                         rendimiento_porcentaje, monto_final, fecha_simulacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        simulacion.id_simulacion,
                        simulacion.id_usuario,
                        simulacion.capital_inicial,
                        simulacion.variacion_nasdaq,
                        simulacion.rendimiento_porcentaje,
                        simulacion.monto_final,
                        simulacion.fecha_simulacion,
                    ),
                )
        except errores_psycopg.ForeignKeyViolation as error:
            raise UsuarioNoEncontradoError(simulacion.id_usuario) from error
        except errores_psycopg.InvalidTextRepresentation as error:
            raise IdentificadorInvalidoError(simulacion.id_usuario) from error

    def listar_por_usuario(self, id_usuario: str) -> list[Simulacion]:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    CREATE TABLE IF NOT EXISTS simulaciones (
                        id TEXT PRIMARY KEY,
                        id_usuario TEXT NOT NULL,
                        capital_inicial REAL NOT NULL,
                        variacion_nasdaq REAL NOT NULL,
                        rendimiento_porcentaje REAL NOT NULL,
                        monto_final REAL NOT NULL,
                        fecha_simulacion TEXT NOT NULL,
                        FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
                    )
                    """
                )
                filas = conexion.execute(
                    "SELECT id, id_usuario, capital_inicial, variacion_nasdaq, rendimiento_porcentaje, monto_final, fecha_simulacion FROM simulaciones WHERE id_usuario = ? ORDER BY fecha_simulacion DESC",
                    (id_usuario,),
                ).fetchall()
            return [
                Simulacion(
                    id_simulacion=str(fila["id"]),
                    id_usuario=str(fila["id_usuario"]),
                    capital_inicial=decimal_desde_bd(fila["capital_inicial"]),
                    variacion_nasdaq=decimal_desde_bd(fila["variacion_nasdaq"]),
                    rendimiento_porcentaje=decimal_desde_bd(fila["rendimiento_porcentaje"]),
                    monto_final=decimal_desde_bd(fila["monto_final"]),
                    fecha_simulacion=datetime_desde_bd(fila["fecha_simulacion"]),
                )
                for fila in filas
            ]

        # dict_row (no class_row) porque Postgres devuelve `id`/`id_usuario`
        # como objetos UUID; hay que forzarlos a str para respetar el tipo
        # declarado en Simulacion (y para que RespuestaSimulacion los valide).
        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                cursor = conexion.cursor(row_factory=dict_row)
                cursor.execute(
                    """
                    SELECT id, id_usuario, capital_inicial, variacion_nasdaq,
                           rendimiento_porcentaje, monto_final, fecha_simulacion
                    FROM simulaciones
                    WHERE id_usuario = %s
                    ORDER BY fecha_simulacion DESC
                    """,
                    (id_usuario,),
                )
                return [
                    Simulacion(
                        id_simulacion=str(fila["id"]),
                        id_usuario=str(fila["id_usuario"]),
                        capital_inicial=fila["capital_inicial"],
                        variacion_nasdaq=fila["variacion_nasdaq"],
                        rendimiento_porcentaje=fila["rendimiento_porcentaje"],
                        monto_final=fila["monto_final"],
                        fecha_simulacion=fila["fecha_simulacion"],
                    )
                    for fila in cursor.fetchall()
                ]
        except errores_psycopg.InvalidTextRepresentation as error:
            raise IdentificadorInvalidoError(id_usuario) from error
