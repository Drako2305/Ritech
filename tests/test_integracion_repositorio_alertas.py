"""Prueba de integración: guarda y consulta alertas de verdad en PostgreSQL.

No corre en `pytest` normal (necesita una base de datos real). Para
ejecutarla, con Postgres corriendo y el esquema de db/schema.sql aplicado:

    pytest -m integracion
"""

import os
from decimal import Decimal

import psycopg
import pytest

from api.esquemas import RespuestaAlerta
from dominio.alerta import Alerta
from dominio.excepciones import IdentificadorInvalidoError
from dominio.simulacion import Simulacion
from servicios.repositorio_alertas import RepositorioAlertasPostgres
from servicios.repositorio_simulaciones import RepositorioSimulacionesPostgres

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ritech"
)
ID_USUARIO_SEED = "11111111-1111-1111-1111-111111111111"  # ver db/seed.sql

pytestmark = pytest.mark.integracion


def _crear_simulacion() -> Simulacion:
    repositorio_simulaciones = RepositorioSimulacionesPostgres(DATABASE_URL)
    simulacion = Simulacion(
        id_usuario=ID_USUARIO_SEED,
        capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal("1"),
        rendimiento_porcentaje=Decimal("1"),
        monto_final=Decimal("101000"),
    )
    repositorio_simulaciones.guardar(simulacion)
    return simulacion


def test_guarda_una_alerta_real_en_postgres():
    simulacion = _crear_simulacion()
    repositorio = RepositorioAlertasPostgres(DATABASE_URL)
    alerta = Alerta(
        id_simulacion=simulacion.id_simulacion,
        titulo="Título de prueba",
        contenido="Contenido de prueba",
    )

    repositorio.guardar(alerta)

    with psycopg.connect(DATABASE_URL) as conexion:
        fila = conexion.execute(
            "SELECT id_simulacion, titulo, contenido FROM noticias_alertas WHERE id = %s",
            (alerta.id_alerta,),
        ).fetchone()

    assert fila is not None
    assert str(fila[0]) == simulacion.id_simulacion
    assert fila[1] == "Título de prueba"
    assert fila[2] == "Contenido de prueba"


def test_lista_las_alertas_de_un_usuario_via_join():
    simulacion = _crear_simulacion()
    repositorio = RepositorioAlertasPostgres(DATABASE_URL)
    repositorio.guardar(Alerta(
        id_simulacion=simulacion.id_simulacion,
        titulo="Alerta vía JOIN",
        contenido="Debe encontrarse a través de simulaciones.id_usuario",
    ))

    alertas = repositorio.listar_por_usuario(ID_USUARIO_SEED)

    assert len(alertas) >= 1
    assert any(a.titulo == "Alerta vía JOIN" for a in alertas)
    assert all(isinstance(a.id_alerta, str) and isinstance(a.id_simulacion, str) for a in alertas)


def test_las_alertas_leidas_de_postgres_sirven_para_la_respuesta_de_la_api():
    """Reproduce lo que hace GET /alertas/{id}: si `id`/`id_simulacion`
    vinieran como UUID (no str), esto fallaría con un error de Pydantic."""
    simulacion = _crear_simulacion()
    repositorio = RepositorioAlertasPostgres(DATABASE_URL)
    repositorio.guardar(Alerta(
        id_simulacion=simulacion.id_simulacion,
        titulo="Para la respuesta de la API",
        contenido="...",
    ))

    alertas = repositorio.listar_por_usuario(ID_USUARIO_SEED)
    respuestas = [RespuestaAlerta(**a.__dict__) for a in alertas]  # no debe lanzar

    assert all(isinstance(r.id_alerta, str) for r in respuestas)


def test_listar_por_usuario_con_formato_invalido_lanza_identificador_invalido():
    repositorio = RepositorioAlertasPostgres(DATABASE_URL)
    with pytest.raises(IdentificadorInvalidoError):
        repositorio.listar_por_usuario("string")
