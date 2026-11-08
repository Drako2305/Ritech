import pytest

from dominio.excepciones import CredencialesInvalidasError
from dominio.usuario import RolUsuario
from servicios.servicio_autenticacion import ServicioAutenticacion
from tests.dobles import RepositorioUsuariosFalso


def test_registrar_guarda_el_usuario_con_la_contrasena_hasheada():
    servicio = ServicioAutenticacion(repositorio=RepositorioUsuariosFalso())

    usuario = servicio.registrar(
        nombre="Ana", correo="ana@ritech.test", rol=RolUsuario.INVERSIONISTA,
        contrasena="clave123",
    )

    assert usuario.correo == "ana@ritech.test"
    assert usuario.contrasena_hash != "clave123"


def test_iniciar_sesion_exitoso_con_contrasena_correcta():
    repositorio = RepositorioUsuariosFalso()
    servicio = ServicioAutenticacion(repositorio=repositorio)
    servicio.registrar(
        nombre="Ana", correo="ana@ritech.test", rol=RolUsuario.INVERSIONISTA,
        contrasena="clave123",
    )

    usuario = servicio.iniciar_sesion(correo="ana@ritech.test", contrasena="clave123")

    assert usuario.correo == "ana@ritech.test"


def test_iniciar_sesion_falla_con_contrasena_incorrecta():
    repositorio = RepositorioUsuariosFalso()
    servicio = ServicioAutenticacion(repositorio=repositorio)
    servicio.registrar(
        nombre="Ana", correo="ana@ritech.test", rol=RolUsuario.INVERSIONISTA,
        contrasena="clave123",
    )

    with pytest.raises(CredencialesInvalidasError):
        servicio.iniciar_sesion(correo="ana@ritech.test", contrasena="clave-equivocada")


def test_iniciar_sesion_falla_si_el_correo_no_existe():
    servicio = ServicioAutenticacion(repositorio=RepositorioUsuariosFalso())

    with pytest.raises(CredencialesInvalidasError):
        servicio.iniciar_sesion(correo="no-existe@ritech.test", contrasena="lo-que-sea")
