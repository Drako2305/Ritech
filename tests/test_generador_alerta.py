import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import requests

from dominio.excepciones import ErrorGeneracionAlerta
from dominio.noticia import Noticia
from dominio.simulacion import Simulacion
from servicios.generador_alerta import GeneradorAlertaGemini
from tests.dobles import ProveedorNoticiasFalso

RUTA_POST = "servicios.generador_alerta.requests.post"

SIMULACION = Simulacion(
    id_usuario="11111111-1111-1111-1111-111111111111",
    capital_inicial=Decimal("200000"),
    variacion_nasdaq=Decimal("2"),
    rendimiento_porcentaje=Decimal("2"),
    monto_final=Decimal("204000"),
)


def _respuesta(texto: str) -> MagicMock:
    respuesta = MagicMock()
    respuesta.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": texto}]}}]
    }
    return respuesta


def test_retorna_titulo_y_contenido_generados_por_gemini_a_partir_de_noticias():
    cuerpo = json.dumps({"titulo": "Mercado al alza", "contenido": "Las noticias son positivas."})
    proveedor = ProveedorNoticiasFalso([Noticia(titulo="NASDAQ sube", resumen="Buen trimestre")])
    with patch(RUTA_POST, return_value=_respuesta(cuerpo)) as mock_post:
        generador = GeneradorAlertaGemini(proveedor_noticias=proveedor, api_key="clave-falsa")
        titulo, contenido = generador.generar(SIMULACION)

    assert titulo == "Mercado al alza"
    assert contenido == "Las noticias son positivas."
    # El prompt enviado a Gemini debe incluir el contenido de la noticia real.
    prompt_enviado = mock_post.call_args.kwargs["json"]["contents"][0]["parts"][0]["text"]
    assert "NASDAQ sube" in prompt_enviado
    assert "Buen trimestre" in prompt_enviado


def test_lanza_error_si_falla_la_consulta_de_noticias():
    proveedor = ProveedorNoticiasFalso(debe_fallar=True)
    generador = GeneradorAlertaGemini(proveedor_noticias=proveedor, api_key="clave-falsa")

    with pytest.raises(ErrorGeneracionAlerta):
        generador.generar(SIMULACION)


def test_sin_clave_gemini_falla_sin_consultar_noticias():
    proveedor = ProveedorNoticiasFalso()
    generador = GeneradorAlertaGemini(proveedor_noticias=proveedor, api_key="")

    with pytest.raises(ErrorGeneracionAlerta, match="clave de Gemini"):
        generador.generar(SIMULACION)


def test_lanza_error_si_falla_la_conexion_con_gemini():
    proveedor = ProveedorNoticiasFalso()
    with patch(RUTA_POST, side_effect=requests.ConnectionError()):
        generador = GeneradorAlertaGemini(proveedor_noticias=proveedor, api_key="clave-falsa")
        with pytest.raises(ErrorGeneracionAlerta):
            generador.generar(SIMULACION)


def test_lanza_error_si_la_respuesta_no_trae_json_valido():
    proveedor = ProveedorNoticiasFalso()
    with patch(RUTA_POST, return_value=_respuesta("esto no es json")):
        generador = GeneradorAlertaGemini(proveedor_noticias=proveedor, api_key="clave-falsa")
        with pytest.raises(ErrorGeneracionAlerta):
            generador.generar(SIMULACION)


def test_lanza_error_si_falta_el_campo_titulo():
    cuerpo = json.dumps({"contenido": "Sin título"})
    proveedor = ProveedorNoticiasFalso()
    with patch(RUTA_POST, return_value=_respuesta(cuerpo)):
        generador = GeneradorAlertaGemini(proveedor_noticias=proveedor, api_key="clave-falsa")
        with pytest.raises(ErrorGeneracionAlerta):
            generador.generar(SIMULACION)
