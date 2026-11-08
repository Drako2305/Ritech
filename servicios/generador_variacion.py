"""Fuentes de la variación diaria del NASDAQ 100.

Se define una interfaz (GeneradorVariacionNasdaq) para que el resto del
sistema no dependa de "cómo" se obtiene el dato: hoy la lee de una API
financiera real, pero podría cambiar de fuente sin tocar MotorSimulacion.
"""

from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
import json
import os

import requests

from dominio.excepciones import ErrorGeneracionVariacion


class GeneradorVariacionNasdaq(ABC):
    """Contrato: cualquier fuente de variación del NASDAQ debe cumplirlo."""

    @abstractmethod
    def generar_variacion(self) -> Decimal:
        """Retorna la variación porcentual del día (puede ser negativa)."""
        raise NotImplementedError


class GeneradorVariacionIA(GeneradorVariacionNasdaq):
    """Usa la API de Claude para generar un valor plausible de variación.

    No consulta datos de mercado reales: le pide al modelo que simule un
    valor de variación diaria típico del índice NASDAQ 100.
    """

    def __init__(self, api_key: str | None = None, modelo: str = "claude-sonnet-5"):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._modelo = modelo

    def generar_variacion(self) -> Decimal:
        prompt = (
            "Genera un valor plausible de variación porcentual diaria del "
            "índice NASDAQ 100, como el cierre de un día normal de mercado "
            "(positivo o negativo, típicamente entre -3 y 3). Responde "
            'ÚNICAMENTE con un JSON de la forma {"variacion_porcentaje": '
            "<numero>}, sin texto adicional."
        )
        try:
            respuesta = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._modelo,
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=10,
            )
            respuesta.raise_for_status()
            texto = respuesta.json()["content"][0]["text"]
            valor = json.loads(texto)["variacion_porcentaje"]
            return Decimal(str(valor))
        except (requests.RequestException, KeyError, IndexError,
                json.JSONDecodeError, InvalidOperation) as error:
            raise ErrorGeneracionVariacion(
                "No se pudo generar la variación del NASDAQ con la IA."
            ) from error


class GeneradorVariacionGemini(GeneradorVariacionNasdaq):
    """Igual que GeneradorVariacionIA, pero usa la API de Gemini (capa gratuita).

    Requiere la variable de entorno GEMINI_API_KEY (se crea en Google AI Studio).
    """

    URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str | None = None, modelo: str = "gemini-3.8-flash"):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._modelo = modelo

    def generar_variacion(self) -> Decimal:
        prompt = (
            "Genera un valor plausible de variación porcentual diaria del "
            "índice NASDAQ 100, como el cierre de un día normal de mercado "
            "(positivo o negativo, típicamente entre -3 y 3). Responde "
            'ÚNICAMENTE con un JSON de la forma {"variacion_porcentaje": '
            "<numero>}."
        )
        try:
            respuesta = requests.post(
                f"{self.URL_BASE}/{self._modelo}:generateContent",
                headers={
                    "x-goog-api-key": self._api_key,
                    "content-type": "application/json",
                },
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                },
                timeout=10,
            )
            respuesta.raise_for_status()
            texto = respuesta.json()["candidates"][0]["content"]["parts"][0]["text"]
            valor = json.loads(texto)["variacion_porcentaje"]
            return Decimal(str(valor))
        except (requests.RequestException, KeyError, IndexError, TypeError,
                json.JSONDecodeError, InvalidOperation) as error:
            raise ErrorGeneracionVariacion(
                "No se pudo generar la variación del NASDAQ con Gemini."
            ) from error


class GeneradorVariacionAlphaVantage(GeneradorVariacionNasdaq):
    """Obtiene la variación diaria REAL desde la API de Alpha Vantage.

    Usa por defecto el símbolo QQQ (ETF que replica el NASDAQ 100), porque las
    capas gratuitas suelen cubrir ETFs y acciones; el índice como tal puede
    requerir un plan de pago. Requiere la variable ALPHAVANTAGE_API_KEY.
    """

    URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, simbolo: str = "QQQ"):
        self._api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
        self._simbolo = simbolo

    def generar_variacion(self) -> Decimal:
        try:
            respuesta = requests.get(
                self.URL,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": self._simbolo,
                    "apikey": self._api_key,
                },
                timeout=10,
            )
            respuesta.raise_for_status()
            # Alpha Vantage responde 200 incluso en errores/límite de uso:
            # en ese caso "Global Quote" no existe o viene vacío (KeyError).
            cotizacion = respuesta.json()["Global Quote"]
            porcentaje = cotizacion["10. change percent"].strip().rstrip("%")
            return Decimal(porcentaje)
        except (requests.RequestException, KeyError, AttributeError,
                ValueError, InvalidOperation) as error:
            raise ErrorGeneracionVariacion(
                "No se pudo obtener la variación del NASDAQ 100 desde Alpha Vantage."
            ) from error


class GeneradorVariacionYahoo(GeneradorVariacionNasdaq):
    """Obtiene la variación diaria de QQQ desde Yahoo Finance, sin API key."""

    URL_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self, simbolo: str = "QQQ"):
        self._simbolo = simbolo

    def generar_variacion(self) -> Decimal:
        try:
            respuesta = requests.get(
                f"{self.URL_BASE}/{self._simbolo}",
                params={"range": "5d", "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0 RiTech/1.0"},
                timeout=10,
            )
            respuesta.raise_for_status()
            resultado = respuesta.json()["chart"]["result"][0]
            porcentaje = resultado["meta"]["regularMarketChangePercent"]
            variacion = Decimal(str(porcentaje))
            if not variacion.is_finite():
                raise ValueError("La cotización devolvió una variación no válida.")
            return variacion
        except (
            requests.RequestException,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            InvalidOperation,
        ) as error:
            raise ErrorGeneracionVariacion(
                "No se pudo obtener la variación reciente de QQQ desde Yahoo Finance."
            ) from error


class GeneradorVariacionConRespaldo(GeneradorVariacionNasdaq):
    """Intenta una fuente primaria y usa una fuente real alternativa si falla."""

    def __init__(
        self,
        primario: GeneradorVariacionNasdaq,
        respaldo: GeneradorVariacionNasdaq,
    ):
        self._primario = primario
        self._respaldo = respaldo

    def generar_variacion(self) -> Decimal:
        try:
            return self._primario.generar_variacion()
        except ErrorGeneracionVariacion:
            return self._respaldo.generar_variacion()
