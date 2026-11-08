"""Orquesta una simulación de inversión: valida el capital, obtiene la
variación del NASDAQ y calcula el rendimiento.
"""

from decimal import Decimal

from dominio.excepciones import CapitalInsuficienteError
from dominio.simulacion import Simulacion
from servicios.calculadora_rendimiento import CalculadoraRendimientoSimetrico
from servicios.generador_variacion import GeneradorVariacionNasdaq


class MotorSimulacion:
    CAPITAL_MINIMO = Decimal("100000")

    def __init__(
        self,
        generador_variacion: GeneradorVariacionNasdaq,
        calculadora: CalculadoraRendimientoSimetrico | None = None,
        capital_minimo: Decimal = CAPITAL_MINIMO,
    ):
        self._generador_variacion = generador_variacion
        self._calculadora = calculadora or CalculadoraRendimientoSimetrico()
        self._capital_minimo = capital_minimo

    def ejecutar_simulacion(
        self,
        id_usuario: str,
        capital_inicial: Decimal,
        variacion_nasdaq: Decimal | None = None,
    ) -> Simulacion:
        self._validar_capital(capital_inicial)
        if variacion_nasdaq is None:
            variacion_nasdaq = self._generador_variacion.generar_variacion()
        else:
            variacion_nasdaq = Decimal(str(variacion_nasdaq))
        rendimiento_porcentaje, monto_final = self._calculadora.calcular(
            capital_inicial, variacion_nasdaq
        )
        return Simulacion(
            id_usuario=id_usuario,
            capital_inicial=capital_inicial,
            variacion_nasdaq=variacion_nasdaq,
            rendimiento_porcentaje=rendimiento_porcentaje,
            monto_final=monto_final,
        )

    def _validar_capital(self, capital_inicial: Decimal) -> None:
        if capital_inicial < self._capital_minimo:
            raise CapitalInsuficienteError(capital_inicial, self._capital_minimo)
