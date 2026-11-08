"""Persistencia de alertas (tabla noticias_alertas)."""

from abc import ABC, abstractmethod
import sqlite3
from datetime import datetime

import psycopg
from psycopg import errors as errores_psycopg
from psycopg.rows import dict_row

from dominio.alerta import Alerta
from dominio.excepciones import IdentificadorInvalidoError
from servicios.sqlite_compat import abrir_conexion, datetime_a_bd, datetime_desde_bd, es_sqlite


class RepositorioAlertas(ABC):
    """Contrato: cualquier forma de guardar/consultar alertas debe cumplirlo."""

    @abstractmethod
    def guardar(self, alerta: Alerta) -> None:
        raise NotImplementedError

    @abstractmethod
    def listar_por_usuario(self, id_usuario: str) -> list[Alerta]:
        raise NotImplementedError


class RepositorioAlertasPostgres(RepositorioAlertas):
    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion

    def guardar(self, alerta: Alerta) -> None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    CREATE TABLE IF NOT EXISTS noticias_alertas (
                        id TEXT PRIMARY KEY,
                        id_simulacion TEXT NOT NULL,
                        titulo TEXT NOT NULL,
                        contenido TEXT NOT NULL,
                        generado_por_ia INTEGER NOT NULL DEFAULT 1,
                        creado_en TEXT NOT NULL,
                        FOREIGN KEY (id_simulacion) REFERENCES simulaciones(id)
                    )
                    """
                )
                conexion.execute(
                    "INSERT INTO noticias_alertas (id, id_simulacion, titulo, contenido, generado_por_ia, creado_en) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        alerta.id_alerta,
                        alerta.id_simulacion,
                        alerta.titulo,
                        alerta.contenido,
                        int(bool(alerta.generado_por_ia)),
                        datetime_a_bd(alerta.creado_en),
                    ),
                )
            return

        with psycopg.connect(self._cadena_conexion) as conexion:
            conexion.execute(
                """
                INSERT INTO noticias_alertas
                    (id, id_simulacion, titulo, contenido, generado_por_ia, creado_en)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    alerta.id_alerta,
                    alerta.id_simulacion,
                    alerta.titulo,
                    alerta.contenido,
                    alerta.generado_por_ia,
                    alerta.creado_en,
                ),
            )

    def listar_por_usuario(self, id_usuario: str) -> list[Alerta]:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    CREATE TABLE IF NOT EXISTS noticias_alertas (
                        id TEXT PRIMARY KEY,
                        id_simulacion TEXT NOT NULL,
                        titulo TEXT NOT NULL,
                        contenido TEXT NOT NULL,
                        generado_por_ia INTEGER NOT NULL DEFAULT 1,
                        creado_en TEXT NOT NULL,
                        FOREIGN KEY (id_simulacion) REFERENCES simulaciones(id)
                    )
                    """
                )
                filas = conexion.execute(
                    """
                    SELECT na.id, na.id_simulacion, na.titulo, na.contenido, na.generado_por_ia, na.creado_en
                    FROM noticias_alertas na
                    JOIN simulaciones s ON s.id = na.id_simulacion
                    WHERE s.id_usuario = ?
                    ORDER BY na.creado_en DESC
                    """,
                    (id_usuario,),
                ).fetchall()
            return [
                Alerta(
                    id_alerta=str(fila["id"]),
                    id_simulacion=str(fila["id_simulacion"]),
                    titulo=fila["titulo"],
                    contenido=fila["contenido"],
                    generado_por_ia=bool(fila["generado_por_ia"]),
                    creado_en=datetime_desde_bd(fila["creado_en"]),
                )
                for fila in filas
            ]

        # dict_row (no class_row) por el mismo motivo que en los otros
        # repositorios: hay que forzar los `id` UUID de Postgres a str.
        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                cursor = conexion.cursor(row_factory=dict_row)
                cursor.execute(
                    """
                    SELECT na.id, na.id_simulacion, na.titulo, na.contenido,
                           na.generado_por_ia, na.creado_en
                    FROM noticias_alertas na
                    JOIN simulaciones s ON s.id = na.id_simulacion
                    WHERE s.id_usuario = %s
                    ORDER BY na.creado_en DESC
                    """,
                    (id_usuario,),
                )
                return [
                    Alerta(
                        id_alerta=str(fila["id"]),
                        id_simulacion=str(fila["id_simulacion"]),
                        titulo=fila["titulo"],
                        contenido=fila["contenido"],
                        generado_por_ia=fila["generado_por_ia"],
                        creado_en=fila["creado_en"],
                    )
                    for fila in cursor.fetchall()
                ]
        except errores_psycopg.InvalidTextRepresentation as error:
            raise IdentificadorInvalidoError(id_usuario) from error
