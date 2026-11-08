"""Cálculo simétrico del rendimiento financiero de una simulación."""

from decimal import Decimal


class CalculadoraRendimientoSimetrico:
    """Modelo simétrico: RiTech SAS gana/pierde el DOBLE de la variación del
    NASDAQ 100 (si el índice sube 2%, RiTech gana 4%; si baja 2%, RiTech
    pierde 4%), tanto si la variación es positiva como negativa. El monto
    final se ajusta con ese porcentaje ya duplicado sobre el capital inicial.
    """

    MULTIPLICADOR = Decimal("2")

    def calcular(
        self, capital_inicial: Decimal, variacion_nasdaq: Decimal
    ) -> tuple[Decimal, Decimal]:
        rendimiento_porcentaje = variacion_nasdaq * self.MULTIPLICADOR
        monto_final = capital_inicial * (
            Decimal("1") + rendimiento_porcentaje / Decimal("100")
        )
        return rendimiento_porcentaje, monto_final
