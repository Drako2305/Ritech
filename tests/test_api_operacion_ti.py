from decimal import Decimal

from fastapi.testclient import TestClient

from api.dependencias import obtener_servicio_operacion_ti
from api.main import app
from dominio.estadisticas import Estadisticas
from dominio.usuario import RolUsuario, Usuario
from servicios.servicio_operacion_ti import ServicioOperacionTI
from tests.dobles import RepositorioEstadisticasFalso, RepositorioUsuariosFalso


def _preparar():
    usuarios = RepositorioUsuariosFalso()
    estadisticas = RepositorioEstadisticasFalso(
        Estadisticas(
            total_usuarios=3,
            total_simulaciones=7,
            capital_total_simulado=Decimal("2500000"),
            rendimiento_promedio=Decimal("1.75"),
        )
    )
    servicio = ServicioOperacionTI(usuarios, estadisticas)
    app.dependency_overrides[obtener_servicio_operacion_ti] = lambda: servicio
    gestor = Usuario(
        nombre="Carlos",
        correo="gestor@ritechqa.co",
        rol=RolUsuario.GESTOR_TI,
        contrasena_hash="hash",
    )
    admin = Usuario(
        nombre="Admin",
        correo="admin@ritechqa.co",
        rol=RolUsuario.ADMINISTRADOR,
        contrasena_hash="hash",
    )
    usuarios.crear(gestor)
    usuarios.crear(admin)
    return TestClient(app), gestor, admin


def test_gestor_ti_puede_consultar_estado_operativo():
    client, gestor, _ = _preparar()

    respuesta = client.get(
        "/dashboard/operacion",
        params={"id_usuario_solicitante": gestor.id_usuario},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado_api"] == "Operativa"
    assert respuesta.json()["total_simulaciones"] == 7
    app.dependency_overrides.clear()


def test_otros_roles_no_pueden_consultar_estado_operativo():
    client, _, admin = _preparar()

    respuesta = client.get(
        "/dashboard/operacion",
        params={"id_usuario_solicitante": admin.id_usuario},
    )

    assert respuesta.status_code == 403
    app.dependency_overrides.clear()
