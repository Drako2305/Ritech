from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import requests

from dominio.excepciones import ErrorGeneracionVariacion
from servicios.generador_variacion import (
    GeneradorVariacionAlphaVantage,
    GeneradorVariacionYahoo,
)

RUTA_GET = "servicios.generador_variacion.requests.get"


def _respuesta(cuerpo: dict) -> MagicMock:
    respuesta = MagicMock()
    respuesta.json.return_value = cuerpo
    return respuesta


def test_retorna_variacion_negativa_sin_el_simbolo_porcentaje():
    cuerpo = {"Global Quote": {"10. change percent": "-0.9107%"}}
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        generador = GeneradorVariacionAlphaVantage(api_key="clave-falsa")
        assert generador.generar_variacion() == Decimal("-0.9107")


def test_retorna_variacion_positiva():
    cuerpo = {"Global Quote": {"10. change percent": "1.2500%"}}
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        generador = GeneradorVariacionAlphaVantage(api_key="clave-falsa")
        assert generador.generar_variacion() == Decimal("1.25")


def test_lanza_error_si_se_supera_el_limite_de_uso():
    cuerpo = {"Information": "Se alcanzó el límite diario de solicitudes."}
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        generador = GeneradorVariacionAlphaVantage(api_key="clave-falsa")
        with pytest.raises(ErrorGeneracionVariacion):
            generador.generar_variacion()


def test_lanza_error_si_la_cotizacion_viene_vacia():
    with patch(RUTA_GET, return_value=_respuesta({"Global Quote": {}})):
        generador = GeneradorVariacionAlphaVantage(api_key="clave-falsa")
        with pytest.raises(ErrorGeneracionVariacion):
            generador.generar_variacion()


def test_lanza_error_si_falla_la_conexion():
    with patch(RUTA_GET, side_effect=requests.ConnectionError()):
        generador = GeneradorVariacionAlphaVantage(api_key="clave-falsa")
        with pytest.raises(ErrorGeneracionVariacion):
            generador.generar_variacion()


def test_yahoo_retorna_variacion_real_de_qqq():
    cuerpo = {
        "chart": {
            "result": [{"meta": {"regularMarketChangePercent": 1.399}}],
            "error": None,
        }
    }
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        generador = GeneradorVariacionYahoo()
        assert generador.generar_variacion() == Decimal("1.399")
