from decimal import Decimal

from dominio.excepciones import ErrorGeneracionAlerta
from dominio.simulacion import Simulacion
from servicios.generador_alerta import (
    GeneradorAlerta,
    GeneradorAlertaConRespaldo,
    GeneradorAlertaLocal,
)


def _simulacion(rendimiento: str, monto_final: str) -> Simulacion:
    return Simulacion(
        id_usuario="u1",
        capital_inicial=Decimal("100000"),
        variacion_nasdaq=Decimal(rendimiento) / Decimal("2"),
        rendimiento_porcentaje=Decimal(rendimiento),
        monto_final=Decimal(monto_final),
    )


def test_alerta_local_para_escenario_alcista():
    titulo, contenido = GeneradorAlertaLocal().generar(_simulacion("4", "104000"))
    assert "alcista" in titulo.lower()
    assert "$104,000" in contenido
    assert "ganancia" in contenido.lower()


def test_alerta_local_para_escenario_bajista():
    titulo, contenido = GeneradorAlertaLocal().generar(_simulacion("-4", "96000"))
    assert "bajista" in titulo.lower()
    assert "$96,000" in contenido
    assert "pérdida" in contenido.lower()


class GeneradorQueFalla(GeneradorAlerta):
    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        raise ErrorGeneracionAlerta("Sin IA configurada.")


class GeneradorQueResponde(GeneradorAlerta):
    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        return "Título IA", "Contenido IA"


def test_usa_el_respaldo_local_cuando_la_ia_falla():
    generador = GeneradorAlertaConRespaldo(
        primario=GeneradorQueFalla(), respaldo=GeneradorAlertaLocal()
    )
    titulo, _ = generador.generar(_simulacion("4", "104000"))
    assert "alcista" in titulo.lower()


def test_prefiere_la_ia_cuando_esta_disponible():
    generador = GeneradorAlertaConRespaldo(
        primario=GeneradorQueResponde(), respaldo=GeneradorAlertaLocal()
    )
    assert generador.generar(_simulacion("4", "104000")) == ("Título IA", "Contenido IA")
