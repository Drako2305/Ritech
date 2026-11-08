from unittest.mock import MagicMock, patch

import pytest
import requests

from dominio.excepciones import ErrorConsultaNoticias
from servicios.proveedor_noticias import ProveedorNoticiasAlphaVantage

RUTA_GET = "servicios.proveedor_noticias.requests.get"


def _respuesta(cuerpo: dict) -> MagicMock:
    respuesta = MagicMock()
    respuesta.json.return_value = cuerpo
    return respuesta


def test_retorna_las_noticias_del_feed():
    cuerpo = {
        "feed": [
            {"title": "NASDAQ cierra al alza", "summary": "Tecnológicas impulsan el índice."},
            {"title": "Inflación preocupa a inversionistas", "summary": "La Fed podría subir tasas."},
        ]
    }
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        proveedor = ProveedorNoticiasAlphaVantage(api_key="clave-falsa")
        noticias = proveedor.obtener_noticias()

    assert len(noticias) == 2
    assert noticias[0].titulo == "NASDAQ cierra al alza"
    assert noticias[0].resumen == "Tecnológicas impulsan el índice."


def test_respeta_el_limite():
    cuerpo = {"feed": [{"title": f"Noticia {i}", "summary": "..."} for i in range(10)]}
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        proveedor = ProveedorNoticiasAlphaVantage(api_key="clave-falsa")
        noticias = proveedor.obtener_noticias(limite=3)

    assert len(noticias) == 3


def test_lanza_error_si_se_supera_el_limite_de_uso():
    cuerpo = {"Information": "Se alcanzó el límite diario de solicitudes."}
    with patch(RUTA_GET, return_value=_respuesta(cuerpo)):
        proveedor = ProveedorNoticiasAlphaVantage(api_key="clave-falsa")
        with pytest.raises(ErrorConsultaNoticias):
            proveedor.obtener_noticias()


def test_lanza_error_si_falla_la_conexion():
    with patch(RUTA_GET, side_effect=requests.ConnectionError()):
        proveedor = ProveedorNoticiasAlphaVantage(api_key="clave-falsa")
        with pytest.raises(ErrorConsultaNoticias):
            proveedor.obtener_noticias()


    def test_sin_clave_alpha_vantage_falla_sin_esperar_red():
        from dominio.excepciones import ErrorConsultaNoticias

        proveedor = ProveedorNoticiasAlphaVantage(api_key="")
        with pytest.raises(ErrorConsultaNoticias, match="clave de Alpha Vantage"):
            proveedor.obtener_noticias()
