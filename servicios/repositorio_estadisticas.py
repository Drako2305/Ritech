"""Repositorio de solo lectura para los agregados del dashboard.

Es intencionalmente independiente de RepositorioUsuarios/RepositorioSimulaciones:
no escribe nada, solo consulta ambas tablas para armar un resumen.
"""

from abc import ABC, abstractmethod
import sqlite3

import psycopg

from dominio.estadisticas import Estadisticas
from servicios.sqlite_compat import decimal_desde_bd, es_sqlite, abrir_conexion


class RepositorioEstadisticas(ABC):
    """Contrato: cualquier forma de calcular los agregados debe cumplirlo."""

    @abstractmethod
    def obtener(self) -> Estadisticas:
        raise NotImplementedError


class RepositorioEstadisticasPostgres(RepositorioEstadisticas):
    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion

    def obtener(self) -> Estadisticas:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id TEXT PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        correo TEXT NOT NULL UNIQUE,
                        rol TEXT NOT NULL CHECK (rol IN ('INVERSIONISTA', 'GESTOR_TI', 'ADMINISTRADOR')),
                        contrasena_hash TEXT NOT NULL,
                        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
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
                fila = conexion.execute(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM usuarios) AS total_usuarios,
                        (SELECT COUNT(*) FROM simulaciones) AS total_simulaciones,
                        COALESCE((SELECT SUM(capital_inicial) FROM simulaciones), 0) AS capital_total_simulado,
                        COALESCE((SELECT AVG(rendimiento_porcentaje) FROM simulaciones), 0) AS rendimiento_promedio
                    """
                ).fetchone()
            return Estadisticas(
                total_usuarios=fila["total_usuarios"],
                total_simulaciones=fila["total_simulaciones"],
                capital_total_simulado=decimal_desde_bd(fila["capital_total_simulado"]),
                rendimiento_promedio=decimal_desde_bd(fila["rendimiento_promedio"]),
            )

        with psycopg.connect(self._cadena_conexion) as conexion:
            fila = conexion.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM usuarios) AS total_usuarios,
                    COUNT(s.id) AS total_simulaciones,
                    COALESCE(SUM(s.capital_inicial), 0) AS capital_total_simulado,
                    COALESCE(AVG(s.rendimiento_porcentaje), 0) AS rendimiento_promedio
                FROM simulaciones s
                """
            ).fetchone()

        return Estadisticas(
            total_usuarios=fila[0],
            total_simulaciones=fila[1],
            capital_total_simulado=fila[2],
            rendimiento_promedio=fila[3],
        )
