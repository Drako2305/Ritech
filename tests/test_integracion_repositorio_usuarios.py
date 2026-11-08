"""Prueba de integración: guarda y consulta usuarios de verdad en PostgreSQL.

Correr con: pytest -m integracion (requiere Postgres con db/schema.sql aplicado)
"""

import os
import uuid
from decimal import Decimal

import pytest

from api.esquemas import RespuestaUsuario
from dominio.excepciones import (
    CorreoDuplicadoError,
    IdentificadorInvalidoError,
    UsuarioConSimulacionesError,
    UsuarioNoEncontradoError,
)
from dominio.simulacion import Simulacion
from dominio.usuario import RolUsuario, Usuario
from servicios.repositorio_simulaciones import RepositorioSimulacionesPostgres
from servicios.autenticador import Autenticador
from servicios.repositorio_usuarios import RepositorioUsuariosPostgres

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ritech"
)

pytestmark = pytest.mark.integracion


def _usuario_de_prueba() -> Usuario:
    correo = f"integracion-{uuid.uuid4()}@ritech.test"
    contrasena_hash = Autenticador().hashear("clave123")
    return Usuario(
        nombre="Usuario de integración", correo=correo,
        rol=RolUsuario.INVERSIONISTA, contrasena_hash=contrasena_hash,
    )


def test_crea_y_luego_encuentra_el_usuario_por_correo():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()

    repositorio.crear(usuario)
    encontrado = repositorio.buscar_por_correo(usuario.correo)

    assert encontrado is not None
    assert encontrado.correo == usuario.correo
    assert encontrado.contrasena_hash == usuario.contrasena_hash


def test_buscar_por_correo_retorna_none_si_no_existe():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    assert repositorio.buscar_por_correo("no-existe-nunca@ritech.test") is None


def test_rechaza_correo_duplicado():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio.crear(usuario)

    duplicado = Usuario(
        nombre="Otro nombre", correo=usuario.correo,
        rol=RolUsuario.ADMINISTRADOR, contrasena_hash=usuario.contrasena_hash,
    )
    with pytest.raises(CorreoDuplicadoError):
        repositorio.crear(duplicado)


def test_el_usuario_leido_de_postgres_sirve_para_construir_la_respuesta_de_la_api():
    """Reproduce lo que hace /login: si `id` viniera como UUID (no str),
    esto fallaría con un error de validación de Pydantic."""
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio.crear(usuario)

    encontrado = repositorio.buscar_por_correo(usuario.correo)
    respuesta = RespuestaUsuario(**encontrado.__dict__)  # no debe lanzar

    assert respuesta.id_usuario == encontrado.id_usuario
    assert isinstance(respuesta.id_usuario, str)


def test_listar_todos_incluye_el_usuario_creado():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio.crear(usuario)

    correos = {u.correo for u in repositorio.listar_todos()}

    assert usuario.correo in correos


def test_buscar_por_id_encuentra_el_usuario_creado():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio.crear(usuario)

    encontrado = repositorio.buscar_por_id(usuario.id_usuario)

    assert encontrado is not None
    assert encontrado.correo == usuario.correo


def test_actualizar_rol_cambia_el_rol_guardado():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio.crear(usuario)

    repositorio.actualizar_rol(usuario.id_usuario, RolUsuario.GESTOR_TI)

    assert repositorio.buscar_por_id(usuario.id_usuario).rol == RolUsuario.GESTOR_TI


def test_actualizar_rol_de_usuario_inexistente_lanza_no_encontrado():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    with pytest.raises(UsuarioNoEncontradoError):
        repositorio.actualizar_rol("00000000-0000-0000-0000-000000000000", RolUsuario.GESTOR_TI)


def test_eliminar_borra_el_usuario():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio.crear(usuario)

    repositorio.eliminar(usuario.id_usuario)

    assert repositorio.buscar_por_id(usuario.id_usuario) is None


def test_eliminar_usuario_inexistente_lanza_no_encontrado():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    with pytest.raises(UsuarioNoEncontradoError):
        repositorio.eliminar("00000000-0000-0000-0000-000000000000")


def test_eliminar_usuario_con_simulaciones_lanza_error_especifico():
    repositorio_usuarios = RepositorioUsuariosPostgres(DATABASE_URL)
    repositorio_simulaciones = RepositorioSimulacionesPostgres(DATABASE_URL)
    usuario = _usuario_de_prueba()
    repositorio_usuarios.crear(usuario)
    repositorio_simulaciones.guardar(Simulacion(
        id_usuario=usuario.id_usuario, capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal("1"), rendimiento_porcentaje=Decimal("1"),
        monto_final=Decimal("101000"),
    ))

    with pytest.raises(UsuarioConSimulacionesError):
        repositorio_usuarios.eliminar(usuario.id_usuario)


def test_buscar_por_id_con_formato_invalido_lanza_identificador_invalido():
    """Reproduce el caso real: alguien deja el valor de ejemplo "string" de
    Swagger en vez de un UUID."""
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    with pytest.raises(IdentificadorInvalidoError):
        repositorio.buscar_por_id("string")


def test_eliminar_con_formato_invalido_lanza_identificador_invalido():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    with pytest.raises(IdentificadorInvalidoError):
        repositorio.eliminar("string")


def test_actualizar_rol_con_formato_invalido_lanza_identificador_invalido():
    repositorio = RepositorioUsuariosPostgres(DATABASE_URL)
    with pytest.raises(IdentificadorInvalidoError):
        repositorio.actualizar_rol("string", RolUsuario.GESTOR_TI)
