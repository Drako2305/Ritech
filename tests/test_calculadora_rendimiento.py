from decimal import Decimal

from servicios.calculadora_rendimiento import CalculadoraRendimientoSimetrico


def test_variacion_positiva_incrementa_capital_al_doble():
    calculadora = CalculadoraRendimientoSimetrico()
    rendimiento, monto_final = calculadora.calcular(Decimal("100000"), Decimal("3"))
    assert rendimiento == Decimal("6")
    assert monto_final == Decimal("106000")


def test_variacion_negativa_reduce_capital_al_doble():
    calculadora = CalculadoraRendimientoSimetrico()
    rendimiento, monto_final = calculadora.calcular(Decimal("100000"), Decimal("-2"))
    assert rendimiento == Decimal("-4")
    assert monto_final == Decimal("96000")


def test_variacion_cero_no_cambia_el_capital():
    calculadora = CalculadoraRendimientoSimetrico()
    rendimiento, monto_final = calculadora.calcular(Decimal("500000"), Decimal("0"))
    assert rendimiento == Decimal("0")
    assert monto_final == Decimal("500000")
