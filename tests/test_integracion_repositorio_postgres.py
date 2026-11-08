"""Prueba de integración: guarda de verdad en PostgreSQL.

No corre en `pytest` normal (necesita una base de datos real). Para
ejecutarla, con Postgres corriendo y el esquema de db/schema.sql aplicado:

    pytest -m integracion

Usa DATABASE_URL si está definida, o el valor por defecto de desarrollo.
"""

import os
from decimal import Decimal

import psycopg
import pytest

from api.esquemas import RespuestaSimulacion
from dominio.excepciones import IdentificadorInvalidoError, UsuarioNoEncontradoError
from dominio.simulacion import Simulacion
from servicios.repositorio_simulaciones import RepositorioSimulacionesPostgres

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ritech"
)
ID_USUARIO_SEED = "11111111-1111-1111-1111-111111111111"  # ver db/seed.sql

pytestmark = pytest.mark.integracion


def test_guarda_una_simulacion_real_en_postgres():
    repositorio = RepositorioSimulacionesPostgres(DATABASE_URL)
    simulacion = Simulacion(
        id_usuario=ID_USUARIO_SEED,
        capital_inicial=Decimal("150000"),
        variacion_nasdaq=Decimal("1.5"),
        rendimiento_porcentaje=Decimal("1.5"),
        monto_final=Decimal("152250"),
    )

    repositorio.guardar(simulacion)

    with psycopg.connect(DATABASE_URL) as conexion:
        fila = conexion.execute(
            "SELECT id_usuario, capital_inicial FROM simulaciones WHERE id = %s",
            (simulacion.id_simulacion,),
        ).fetchone()

    assert fila is not None
    assert str(fila[0]) == ID_USUARIO_SEED
    assert fila[1] == Decimal("150000.00")


def test_lanza_error_si_el_usuario_no_existe():
    repositorio = RepositorioSimulacionesPostgres(DATABASE_URL)
    simulacion = Simulacion(
        id_usuario="00000000-0000-0000-0000-000000000000",  # no existe en usuarios
        capital_inicial=Decimal("150000"),
        variacion_nasdaq=Decimal("1.5"),
        rendimiento_porcentaje=Decimal("1.5"),
        monto_final=Decimal("152250"),
    )

    with pytest.raises(UsuarioNoEncontradoError):
        repositorio.guardar(simulacion)


def test_lista_las_simulaciones_guardadas_de_un_usuario():
    repositorio = RepositorioSimulacionesPostgres(DATABASE_URL)
    repositorio.guardar(Simulacion(
        id_usuario=ID_USUARIO_SEED, capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal("1"), rendimiento_porcentaje=Decimal("1"),
        monto_final=Decimal("101000"),
    ))

    simulaciones = repositorio.listar_por_usuario(ID_USUARIO_SEED)

    assert len(simulaciones) >= 1
    assert all(str(s.id_usuario) == ID_USUARIO_SEED for s in simulaciones)


def test_las_simulaciones_leidas_de_postgres_sirven_para_la_respuesta_de_la_api():
    """Reproduce lo que hace GET /simulaciones/{id}: si `id`/`id_usuario`
    vinieran como UUID (no str), esto fallaría con un error de Pydantic."""
    repositorio = RepositorioSimulacionesPostgres(DATABASE_URL)
    repositorio.guardar(Simulacion(
        id_usuario=ID_USUARIO_SEED, capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal("1"), rendimiento_porcentaje=Decimal("1"),
        monto_final=Decimal("101000"),
    ))

    simulaciones = repositorio.listar_por_usuario(ID_USUARIO_SEED)
    respuestas = [RespuestaSimulacion(**s.__dict__) for s in simulaciones]  # no debe lanzar

    assert all(isinstance(r.id_usuario, str) for r in respuestas)


def test_listar_por_usuario_con_formato_invalido_lanza_identificador_invalido():
    repositorio = RepositorioSimulacionesPostgres(DATABASE_URL)
    with pytest.raises(IdentificadorInvalidoError):
        repositorio.listar_por_usuario("string")


def test_guardar_con_id_usuario_invalido_lanza_identificador_invalido():
    repositorio = RepositorioSimulacionesPostgres(DATABASE_URL)
    simulacion = Simulacion(
        id_usuario="string", capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal("1"), rendimiento_porcentaje=Decimal("1"),
        monto_final=Decimal("101000"),
    )
    with pytest.raises(IdentificadorInvalidoError):
        repositorio.guardar(simulacion)
