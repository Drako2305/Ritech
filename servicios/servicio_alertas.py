"""Genera y guarda la alerta de una simulación. Es "best-effort": si la IA
falla, no se propaga el error — la simulación ya se guardó y es lo que
importa; la alerta es un extra."""

from dominio.alerta import Alerta
from dominio.excepciones import ErrorGeneracionAlerta
from dominio.simulacion import Simulacion
from servicios.generador_alerta import GeneradorAlerta
from servicios.repositorio_alertas import RepositorioAlertas


class ServicioAlertas:
    def __init__(self, generador: GeneradorAlerta, repositorio: RepositorioAlertas):
        self._generador = generador
        self._repositorio = repositorio

    def generar_y_guardar(self, simulacion: Simulacion) -> Alerta | None:
        try:
            titulo, contenido = self._generador.generar(simulacion)
        except ErrorGeneracionAlerta:
            return None

        alerta = Alerta(
            id_simulacion=simulacion.id_simulacion, titulo=titulo, contenido=contenido
        )
        self._repositorio.guardar(alerta)
        return alerta
