"""Prueba de integración: calcula agregados reales sobre PostgreSQL.

Correr con: pytest -m integracion (requiere Postgres con db/schema.sql aplicado)
"""

import os
from decimal import Decimal

import psycopg
import pytest

from dominio.simulacion import Simulacion
from servicios.repositorio_estadisticas import RepositorioEstadisticasPostgres
from servicios.repositorio_simulaciones import RepositorioSimulacionesPostgres

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ritech"
)
ID_USUARIO_SEED = "11111111-1111-1111-1111-111111111111"  # ver db/seed.sql

pytestmark = pytest.mark.integracion


def test_las_estadisticas_reflejan_los_totales_reales_de_la_base():
    repositorio_simulaciones = RepositorioSimulacionesPostgres(DATABASE_URL)
    repositorio_estadisticas = RepositorioEstadisticasPostgres(DATABASE_URL)

    with psycopg.connect(DATABASE_URL) as conexion:
        totales_antes = conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    repositorio_simulaciones.guardar(Simulacion(
        id_usuario=ID_USUARIO_SEED, capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal("2"), rendimiento_porcentaje=Decimal("2"),
        monto_final=Decimal("102000"),
    ))

    estadisticas = repositorio_estadisticas.obtener()

    assert estadisticas.total_usuarios == totales_antes
    assert estadisticas.total_simulaciones >= 1
    assert estadisticas.capital_total_simulado >= Decimal("100000")
    assert isinstance(estadisticas.rendimiento_promedio, Decimal)
