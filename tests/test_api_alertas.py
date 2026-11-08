from fastapi.testclient import TestClient

from api.dependencias import (
    obtener_repositorio_alertas,
    obtener_servicio_autorizacion_roles,
)
from api.main import app
from dominio.alerta import Alerta
from dominio.usuario import RolUsuario, Usuario
from servicios.servicio_autorizacion_roles import ServicioAutorizacionRoles
from tests.dobles import RepositorioAlertasFalso, RepositorioUsuariosFalso

ID_USUARIO_VALIDO = "11111111-1111-1111-1111-111111111111"


def _preparar(alertas: list[Alerta], id_usuario: str = ID_USUARIO_VALIDO):
    repositorio = RepositorioAlertasFalso()
    repositorio.alertas_guardadas = alertas
    app.dependency_overrides[obtener_repositorio_alertas] = lambda: repositorio
    usuarios = RepositorioUsuariosFalso()
    usuarios.crear(
        Usuario(
            id_usuario=id_usuario,
            nombre="Prueba",
            correo="prueba@ritechqa.co",
            rol=RolUsuario.INVERSIONISTA,
            contrasena_hash="hash",
        )
    )
    app.dependency_overrides[obtener_servicio_autorizacion_roles] = lambda: (
        ServicioAutorizacionRoles(usuarios)
    )
    return TestClient(app)


def test_lista_las_alertas_de_un_usuario():
    alerta = Alerta(id_simulacion="sim-1", titulo="Título", contenido="Contenido")
    client = _preparar([alerta])

    respuesta = client.get(f"/alertas/{ID_USUARIO_VALIDO}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["titulo"] == "Título"
    assert cuerpo[0]["contenido"] == "Contenido"

    app.dependency_overrides.clear()


def test_lista_vacia_si_el_usuario_no_tiene_alertas():
    client = _preparar([])

    respuesta = client.get(f"/alertas/{ID_USUARIO_VALIDO}")

    assert respuesta.status_code == 200
    assert respuesta.json() == []

    app.dependency_overrides.clear()


def test_id_usuario_con_formato_invalido_devuelve_400():
    from dominio.excepciones import IdentificadorInvalidoError

    class RepositorioQueRechaza(RepositorioAlertasFalso):
        def listar_por_usuario(self, id_usuario: str):
            raise IdentificadorInvalidoError(id_usuario)

    client = _preparar([], id_usuario="string")
    app.dependency_overrides[obtener_repositorio_alertas] = RepositorioQueRechaza

    respuesta = client.get("/alertas/string")

    assert respuesta.status_code == 400

    app.dependency_overrides.clear()
