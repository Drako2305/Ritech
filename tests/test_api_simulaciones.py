from decimal import Decimal

from fastapi.testclient import TestClient

from api.dependencias import (
    obtener_motor_simulacion,
    obtener_repositorio_simulaciones,
    obtener_servicio_alertas,
    obtener_servicio_autorizacion_roles,
)
from api.main import app
from dominio.usuario import RolUsuario, Usuario
from servicios.motor_simulacion import MotorSimulacion
from servicios.servicio_autorizacion_roles import ServicioAutorizacionRoles
from servicios.servicio_alertas import ServicioAlertas
from tests.dobles import (
    GeneradorAlertaFalso,
    GeneradorVariacionFalso,
    RepositorioAlertasFalso,
    RepositorioSimulacionesFalso,
    RepositorioUsuariosFalso,
)

ID_USUARIO_VALIDO = "11111111-1111-1111-1111-111111111111"


def _preparar(
    variacion: Decimal,
    usuarios_validos=None,
    alerta_debe_fallar: bool = False,
    rol_usuario: RolUsuario = RolUsuario.INVERSIONISTA,
):
    motor = MotorSimulacion(generador_variacion=GeneradorVariacionFalso(variacion))
    repositorio = RepositorioSimulacionesFalso(usuarios_validos)
    servicio_alertas = ServicioAlertas(
        generador=GeneradorAlertaFalso(
            titulo="Alerta de prueba", contenido="Contenido de prueba",
            debe_fallar=alerta_debe_fallar,
        ),
        repositorio=RepositorioAlertasFalso(),
    )
    app.dependency_overrides[obtener_motor_simulacion] = lambda: motor
    app.dependency_overrides[obtener_repositorio_simulaciones] = lambda: repositorio
    app.dependency_overrides[obtener_servicio_alertas] = lambda: servicio_alertas
    repositorio_usuarios = RepositorioUsuariosFalso()
    if usuarios_validos and ID_USUARIO_VALIDO in usuarios_validos:
        repositorio_usuarios.crear(
            Usuario(
                id_usuario=ID_USUARIO_VALIDO,
                nombre="Prueba",
                correo="prueba@ritechqa.co",
                rol=rol_usuario,
                contrasena_hash="hash",
            )
        )
    app.dependency_overrides[obtener_servicio_autorizacion_roles] = lambda: (
        ServicioAutorizacionRoles(repositorio_usuarios)
    )
    return TestClient(app), repositorio


def test_crea_simulacion_y_la_persiste():
    client, repositorio = _preparar(Decimal("2"), usuarios_validos={ID_USUARIO_VALIDO})

    respuesta = client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "200000"},
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert Decimal(cuerpo["rendimiento_porcentaje"]) == Decimal("4")  # el doble de la variación
    assert Decimal(cuerpo["monto_final"]) == Decimal("208000")
    assert len(repositorio.simulaciones_guardadas) == 1
    assert repositorio.simulaciones_guardadas[0].id_usuario == ID_USUARIO_VALIDO

    app.dependency_overrides.clear()


def test_rechaza_capital_menor_al_minimo_y_no_guarda_nada():
    client, repositorio = _preparar(Decimal("1"), usuarios_validos={ID_USUARIO_VALIDO})

    respuesta = client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "50000"},
    )

    assert respuesta.status_code == 400
    assert repositorio.simulaciones_guardadas == []

    app.dependency_overrides.clear()


def test_gestor_ti_no_puede_crear_simulaciones():
    client, repositorio = _preparar(
        Decimal("2"),
        usuarios_validos={ID_USUARIO_VALIDO},
        rol_usuario=RolUsuario.GESTOR_TI,
    )

    respuesta = client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "200000"},
    )

    assert respuesta.status_code == 403
    assert repositorio.simulaciones_guardadas == []
    app.dependency_overrides.clear()


def test_devuelve_404_si_el_usuario_no_existe():
    client, repositorio = _preparar(Decimal("1"), usuarios_validos=set())

    respuesta = client.post(
        "/simulaciones",
        json={"id_usuario": "usuario-inexistente", "capital_inicial": "200000"},
    )

    assert respuesta.status_code == 404
    assert repositorio.simulaciones_guardadas == []

    app.dependency_overrides.clear()


def test_lista_las_simulaciones_de_un_usuario():
    client, repositorio = _preparar(Decimal("2"), usuarios_validos={ID_USUARIO_VALIDO})
    client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "200000"},
    )
    client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "150000"},
    )

    respuesta = client.get(f"/simulaciones/{ID_USUARIO_VALIDO}")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 2

    app.dependency_overrides.clear()


def test_lista_vacia_si_el_usuario_no_tiene_simulaciones():
    client, _ = _preparar(Decimal("2"), usuarios_validos={ID_USUARIO_VALIDO})

    respuesta = client.get(f"/simulaciones/{ID_USUARIO_VALIDO}")

    assert respuesta.status_code == 200
    assert respuesta.json() == []

    app.dependency_overrides.clear()


def test_la_respuesta_incluye_la_alerta_cuando_la_ia_responde_bien():
    client, _ = _preparar(Decimal("2"), usuarios_validos={ID_USUARIO_VALIDO})

    respuesta = client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "200000"},
    )

    assert respuesta.status_code == 201
    alerta = respuesta.json()["alerta"]
    assert alerta is not None
    assert alerta["titulo"] == "Alerta de prueba"
    assert alerta["contenido"] == "Contenido de prueba"

    app.dependency_overrides.clear()


def test_la_simulacion_se_crea_igual_si_falla_la_generacion_de_la_alerta():
    """La alerta es "best-effort": si la IA falla, la simulación se crea
    y persiste de todas formas, solo que sin alerta."""
    client, repositorio = _preparar(
        Decimal("2"), usuarios_validos={ID_USUARIO_VALIDO}, alerta_debe_fallar=True
    )

    respuesta = client.post(
        "/simulaciones",
        json={"id_usuario": ID_USUARIO_VALIDO, "capital_inicial": "200000"},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["alerta"] is None
    assert len(repositorio.simulaciones_guardadas) == 1

    app.dependency_overrides.clear()


def test_permite_simular_un_escenario_de_variacion_manual():
    """Si el inversionista elige un escenario, se ignora la variación real
    de la fuente y se usa el valor enviado (regla ×2 incluida)."""
    client, repositorio = _preparar(Decimal("9"), usuarios_validos={ID_USUARIO_VALIDO})

    respuesta = client.post(
        "/simulaciones",
        json={
            "id_usuario": ID_USUARIO_VALIDO,
            "capital_inicial": "200000",
            "variacion_nasdaq": "1.5",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert Decimal(cuerpo["variacion_nasdaq"]) == Decimal("1.5")
    assert Decimal(cuerpo["rendimiento_porcentaje"]) == Decimal("3.0")
    assert Decimal(cuerpo["monto_final"]) == Decimal("206000")
    assert len(repositorio.simulaciones_guardadas) == 1

    app.dependency_overrides.clear()
