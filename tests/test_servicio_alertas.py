from decimal import Decimal

from dominio.simulacion import Simulacion
from servicios.servicio_alertas import ServicioAlertas
from tests.dobles import GeneradorAlertaFalso, RepositorioAlertasFalso

SIMULACION = Simulacion(
    id_usuario="11111111-1111-1111-1111-111111111111",
    capital_inicial=Decimal("200000"),
    variacion_nasdaq=Decimal("2"),
    rendimiento_porcentaje=Decimal("2"),
    monto_final=Decimal("204000"),
)


def test_genera_y_guarda_la_alerta_cuando_la_ia_responde_bien():
    repositorio = RepositorioAlertasFalso()
    servicio = ServicioAlertas(
        generador=GeneradorAlertaFalso(titulo="Título", contenido="Contenido"),
        repositorio=repositorio,
    )

    alerta = servicio.generar_y_guardar(SIMULACION)

    assert alerta is not None
    assert alerta.titulo == "Título"
    assert alerta.contenido == "Contenido"
    assert alerta.id_simulacion == SIMULACION.id_simulacion
    assert repositorio.alertas_guardadas == [alerta]


def test_retorna_none_y_no_guarda_nada_si_la_ia_falla():
    """La generación de alertas es "best-effort": si la IA falla, no se
    propaga el error (la simulación ya se guardó antes)."""
    repositorio = RepositorioAlertasFalso()
    servicio = ServicioAlertas(
        generador=GeneradorAlertaFalso(debe_fallar=True),
        repositorio=repositorio,
    )

    alerta = servicio.generar_y_guardar(SIMULACION)

    assert alerta is None
    assert repositorio.alertas_guardadas == []
