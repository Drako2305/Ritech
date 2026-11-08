import pytest

from dominio.excepciones import (
    PermisoDenegadoError,
    UsuarioConSimulacionesError,
    UsuarioNoEncontradoError,
)
from dominio.usuario import RolUsuario, Usuario
from servicios.servicio_administracion_usuarios import ServicioAdministracionUsuarios
from tests.dobles import RepositorioUsuariosFalso


def _crear_usuario(repositorio: RepositorioUsuariosFalso, rol: RolUsuario, correo: str) -> str:
    usuario = Usuario(nombre="Test", correo=correo, rol=rol, contrasena_hash="hash")
    repositorio.crear(usuario)
    return usuario.id_usuario


def test_un_administrador_puede_listar_usuarios():
    repositorio = RepositorioUsuariosFalso()
    id_admin = _crear_usuario(repositorio, RolUsuario.ADMINISTRADOR, "admin@ritechqa.co")
    _crear_usuario(repositorio, RolUsuario.INVERSIONISTA, "inversionista@ritechqa.co")
    servicio = ServicioAdministracionUsuarios(repositorio)

    usuarios = servicio.listar_usuarios(id_admin)

    assert len(usuarios) == 2


def test_un_inversionista_no_puede_listar_usuarios():
    repositorio = RepositorioUsuariosFalso()
    id_inversionista = _crear_usuario(
        repositorio, RolUsuario.INVERSIONISTA, "inversionista@ritechqa.co"
    )
    servicio = ServicioAdministracionUsuarios(repositorio)

    with pytest.raises(PermisoDenegadoError):
        servicio.listar_usuarios(id_inversionista)


def test_un_id_solicitante_inexistente_no_tiene_permisos():
    servicio = ServicioAdministracionUsuarios(RepositorioUsuariosFalso())

    with pytest.raises(PermisoDenegadoError):
        servicio.listar_usuarios("no-existe")


def test_administrador_puede_eliminar_un_usuario():
    repositorio = RepositorioUsuariosFalso()
    id_admin = _crear_usuario(repositorio, RolUsuario.ADMINISTRADOR, "admin@ritechqa.co")
    id_objetivo = _crear_usuario(repositorio, RolUsuario.INVERSIONISTA, "otro@ritechqa.co")
    servicio = ServicioAdministracionUsuarios(repositorio)

    servicio.eliminar_usuario(id_admin, id_objetivo)

    assert repositorio.buscar_por_id(id_objetivo) is None


def test_no_se_puede_eliminar_un_usuario_con_simulaciones():
    repositorio = RepositorioUsuariosFalso(ids_con_simulaciones={"con-simulaciones"})
    id_admin = _crear_usuario(repositorio, RolUsuario.ADMINISTRADOR, "admin@ritechqa.co")
    servicio = ServicioAdministracionUsuarios(repositorio)

    with pytest.raises(UsuarioConSimulacionesError):
        servicio.eliminar_usuario(id_admin, "con-simulaciones")


def test_eliminar_usuario_inexistente_lanza_no_encontrado():
    repositorio = RepositorioUsuariosFalso()
    id_admin = _crear_usuario(repositorio, RolUsuario.ADMINISTRADOR, "admin@ritechqa.co")
    servicio = ServicioAdministracionUsuarios(repositorio)

    with pytest.raises(UsuarioNoEncontradoError):
        servicio.eliminar_usuario(id_admin, "no-existe")


def test_administrador_puede_cambiar_el_rol_de_un_usuario():
    repositorio = RepositorioUsuariosFalso()
    id_admin = _crear_usuario(repositorio, RolUsuario.ADMINISTRADOR, "admin@ritechqa.co")
    id_objetivo = _crear_usuario(repositorio, RolUsuario.INVERSIONISTA, "otro@ritechqa.co")
    servicio = ServicioAdministracionUsuarios(repositorio)

    usuario_actualizado = servicio.cambiar_rol(id_admin, id_objetivo, RolUsuario.GESTOR_TI)

    assert usuario_actualizado.rol == RolUsuario.GESTOR_TI
