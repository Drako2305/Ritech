from decimal import Decimal

from fastapi.testclient import TestClient

from api.dependencias import obtener_servicio_dashboard
from api.main import app
from dominio.estadisticas import Estadisticas
from dominio.usuario import RolUsuario, Usuario
from servicios.servicio_dashboard import ServicioDashboard
from tests.dobles import RepositorioEstadisticasFalso, RepositorioUsuariosFalso

ESTADISTICAS = Estadisticas(
    total_usuarios=2, total_simulaciones=4,
    capital_total_simulado=Decimal("800000"), rendimiento_promedio=Decimal("2.25"),
)


def _preparar():
    repositorio_usuarios = RepositorioUsuariosFalso()
    servicio = ServicioDashboard(
        repositorio_usuarios=repositorio_usuarios,
        repositorio_estadisticas=RepositorioEstadisticasFalso(ESTADISTICAS),
    )
    app.dependency_overrides[obtener_servicio_dashboard] = lambda: servicio

    admin = Usuario(nombre="Admin", correo="admin@ritechqa.co",
                     rol=RolUsuario.ADMINISTRADOR, contrasena_hash="hash")
    inversionista = Usuario(nombre="Ana", correo="ana@ritechqa.co",
                             rol=RolUsuario.INVERSIONISTA, contrasena_hash="hash")
    repositorio_usuarios.crear(admin)
    repositorio_usuarios.crear(inversionista)

    return TestClient(app), admin, inversionista


def test_admin_puede_ver_las_estadisticas():
    client, admin, _ = _preparar()

    respuesta = client.get(
        "/dashboard/estadisticas", params={"id_usuario_solicitante": admin.id_usuario}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total_usuarios"] == 2
    assert cuerpo["total_simulaciones"] == 4
    assert Decimal(cuerpo["capital_total_simulado"]) == Decimal("800000")
    assert Decimal(cuerpo["rendimiento_promedio"]) == Decimal("2.25")

    app.dependency_overrides.clear()


def test_no_admin_recibe_403_al_ver_las_estadisticas():
    client, _, inversionista = _preparar()

    respuesta = client.get(
        "/dashboard/estadisticas", params={"id_usuario_solicitante": inversionista.id_usuario}
    )

    assert respuesta.status_code == 403

    app.dependency_overrides.clear()
