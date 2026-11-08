from fastapi.testclient import TestClient

from api.dependencias import obtener_servicio_autenticacion
from api.main import app
from servicios.servicio_autenticacion import ServicioAutenticacion
from tests.dobles import RepositorioUsuariosFalso


def _preparar():
    repositorio = RepositorioUsuariosFalso()
    servicio = ServicioAutenticacion(repositorio=repositorio)
    app.dependency_overrides[obtener_servicio_autenticacion] = lambda: servicio
    return TestClient(app), repositorio


def test_registra_un_usuario_y_no_expone_la_contrasena():
    client, _ = _preparar()

    respuesta = client.post(
        "/usuarios",
        json={
            "nombre": "Ana",
            "correo": "ana@ritechqa.co",
            "rol": "INVERSIONISTA",
            "contrasena": "clave123",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["correo"] == "ana@ritechqa.co"
    assert "contrasena" not in cuerpo
    assert "contrasena_hash" not in cuerpo

    app.dependency_overrides.clear()


def test_registro_publico_rechaza_roles_internos():
    client, repositorio = _preparar()

    respuesta = client.post(
        "/usuarios",
        json={
            "nombre": "Admin",
            "correo": "admin@ritechqa.co",
            "rol": "ADMINISTRADOR",
            "contrasena": "123456",
        },
    )

    assert respuesta.status_code == 403
    assert repositorio.buscar_por_correo("admin@ritechqa.co") is None
    app.dependency_overrides.clear()


def test_rechaza_correo_duplicado_con_409():
    client, _ = _preparar()
    datos = {
        "nombre": "Ana", "correo": "ana@ritechqa.co",
        "rol": "INVERSIONISTA", "contrasena": "clave123",
    }
    client.post("/usuarios", json=datos)

    respuesta = client.post("/usuarios", json=datos)

    assert respuesta.status_code == 409

    app.dependency_overrides.clear()


def test_login_exitoso_con_credenciales_correctas():
    client, _ = _preparar()
    client.post(
        "/usuarios",
        json={
            "nombre": "Ana", "correo": "ana@ritechqa.co",
            "rol": "INVERSIONISTA", "contrasena": "clave123",
        },
    )

    respuesta = client.post(
        "/login", json={"correo": "ana@ritechqa.co", "contrasena": "clave123"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == "ana@ritechqa.co"

    app.dependency_overrides.clear()


def test_login_rechaza_contrasena_incorrecta_con_401():
    client, _ = _preparar()
    client.post(
        "/usuarios",
        json={
            "nombre": "Ana", "correo": "ana@ritechqa.co",
            "rol": "INVERSIONISTA", "contrasena": "clave123",
        },
    )

    respuesta = client.post(
        "/login", json={"correo": "ana@ritechqa.co", "contrasena": "incorrecta"}
    )

    assert respuesta.status_code == 401

    app.dependency_overrides.clear()


def test_login_rechaza_correo_inexistente_con_401():
    client, _ = _preparar()

    respuesta = client.post(
        "/login", json={"correo": "fantasma@ritechqa.co", "contrasena": "lo-que-sea"}
    )

    assert respuesta.status_code == 401

    app.dependency_overrides.clear()
