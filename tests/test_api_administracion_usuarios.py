from fastapi.testclient import TestClient

from api.dependencias import obtener_servicio_administracion_usuarios
from api.main import app
from dominio.usuario import RolUsuario, Usuario
from servicios.servicio_administracion_usuarios import ServicioAdministracionUsuarios
from tests.dobles import RepositorioUsuariosFalso


def _preparar():
    repositorio = RepositorioUsuariosFalso()
    servicio = ServicioAdministracionUsuarios(repositorio)
    app.dependency_overrides[obtener_servicio_administracion_usuarios] = lambda: servicio

    admin = Usuario(nombre="Admin", correo="admin@ritechqa.co",
                     rol=RolUsuario.ADMINISTRADOR, contrasena_hash="hash")
    inversionista = Usuario(nombre="Ana", correo="ana@ritechqa.co",
                             rol=RolUsuario.INVERSIONISTA, contrasena_hash="hash")
    repositorio.crear(admin)
    repositorio.crear(inversionista)

    return TestClient(app), admin, inversionista, repositorio


def test_admin_puede_listar_usuarios():
    client, admin, _, _ = _preparar()

    respuesta = client.get("/usuarios", params={"id_usuario_solicitante": admin.id_usuario})

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 2
    app.dependency_overrides.clear()


def test_no_admin_recibe_403_al_listar_usuarios():
    client, _, inversionista, _ = _preparar()

    respuesta = client.get(
        "/usuarios", params={"id_usuario_solicitante": inversionista.id_usuario}
    )

    assert respuesta.status_code == 403
    app.dependency_overrides.clear()


def test_admin_puede_ver_un_usuario_especifico():
    client, admin, inversionista, _ = _preparar()

    respuesta = client.get(
        f"/usuarios/{inversionista.id_usuario}",
        params={"id_usuario_solicitante": admin.id_usuario},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == "ana@ritechqa.co"
    app.dependency_overrides.clear()


def test_ver_usuario_inexistente_da_404():
    client, admin, _, _ = _preparar()

    respuesta = client.get(
        "/usuarios/no-existe", params={"id_usuario_solicitante": admin.id_usuario}
    )

    assert respuesta.status_code == 404
    app.dependency_overrides.clear()


def test_admin_puede_eliminar_un_usuario():
    client, admin, inversionista, _ = _preparar()

    respuesta = client.delete(
        f"/usuarios/{inversionista.id_usuario}",
        params={"id_usuario_solicitante": admin.id_usuario},
    )

    assert respuesta.status_code == 204
    app.dependency_overrides.clear()


def test_no_se_puede_eliminar_usuario_con_simulaciones():
    client, admin, inversionista, repositorio = _preparar()
    repositorio._ids_con_simulaciones = {inversionista.id_usuario}

    respuesta = client.delete(
        f"/usuarios/{inversionista.id_usuario}",
        params={"id_usuario_solicitante": admin.id_usuario},
    )

    assert respuesta.status_code == 409
    app.dependency_overrides.clear()


def test_admin_puede_cambiar_el_rol_de_un_usuario():
    client, admin, inversionista, _ = _preparar()

    respuesta = client.patch(
        f"/usuarios/{inversionista.id_usuario}/rol",
        params={"id_usuario_solicitante": admin.id_usuario},
        json={"nuevo_rol": "GESTOR_TI"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "GESTOR_TI"
    app.dependency_overrides.clear()


def test_no_admin_no_puede_cambiar_roles():
    client, _, inversionista, _ = _preparar()

    respuesta = client.patch(
        f"/usuarios/{inversionista.id_usuario}/rol",
        params={"id_usuario_solicitante": inversionista.id_usuario},
        json={"nuevo_rol": "ADMINISTRADOR"},
    )

    assert respuesta.status_code == 403
    app.dependency_overrides.clear()
