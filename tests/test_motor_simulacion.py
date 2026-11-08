from decimal import Decimal

import pytest

from dominio.excepciones import CapitalInsuficienteError
from servicios.motor_simulacion import MotorSimulacion
from tests.dobles import GeneradorVariacionFalso


def test_rechaza_capital_menor_al_minimo():
    motor = MotorSimulacion(generador_variacion=GeneradorVariacionFalso(Decimal("1")))
    with pytest.raises(CapitalInsuficienteError):
        motor.ejecutar_simulacion(id_usuario="u1", capital_inicial=Decimal("50000"))


def test_acepta_capital_igual_al_minimo():
    motor = MotorSimulacion(generador_variacion=GeneradorVariacionFalso(Decimal("1")))
    simulacion = motor.ejecutar_simulacion(id_usuario="u1", capital_inicial=Decimal("100000"))
    assert simulacion.capital_inicial == Decimal("100000")


def test_simulacion_exitosa_con_capital_valido():
    motor = MotorSimulacion(generador_variacion=GeneradorVariacionFalso(Decimal("2.5")))
    simulacion = motor.ejecutar_simulacion(id_usuario="u1", capital_inicial=Decimal("200000"))

    assert simulacion.id_usuario == "u1"
    assert simulacion.variacion_nasdaq == Decimal("2.5")
    assert simulacion.rendimiento_porcentaje == Decimal("5.0")  # el doble de la variación
    assert simulacion.monto_final == Decimal("210000")
