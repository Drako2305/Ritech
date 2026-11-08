"""Fuentes de noticias financieras externas: el insumo que la IA procesa
para sugerir la alerta (en vez de reaccionar solo al % de rendimiento de la
simulación, que era la "decisión cualitativa genérica" a evitar)."""

from abc import ABC, abstractmethod
import os

import requests

from dominio.excepciones import ErrorConsultaNoticias
from dominio.noticia import Noticia


class ProveedorNoticiasFinancieras(ABC):
    """Contrato: cualquier fuente de noticias financieras debe cumplirlo."""

    @abstractmethod
    def obtener_noticias(self, limite: int = 5) -> list[Noticia]:
        raise NotImplementedError


class ProveedorNoticiasAlphaVantage(ProveedorNoticiasFinancieras):
    """Usa el endpoint NEWS_SENTIMENT de Alpha Vantage (misma API/clave que
    ya se usa para la variación del NASDAQ 100, capa gratuita)."""

    URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, simbolo: str = "QQQ"):
        self._api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
        self._simbolo = simbolo

    def obtener_noticias(self, limite: int = 5) -> list[Noticia]:
        if not self._api_key:
            raise ErrorConsultaNoticias("No se configuró la clave de Alpha Vantage.")

        try:
            respuesta = requests.get(
                self.URL,
                params={
                    "function": "NEWS_SENTIMENT",
                    "tickers": self._simbolo,
                    "limit": limite,
                    "apikey": self._api_key,
                },
                timeout=10,
            )
            respuesta.raise_for_status()
            # Igual que GLOBAL_QUOTE: Alpha Vantage responde 200 incluso en
            # errores/límite de uso; en ese caso "feed" no existe (KeyError).
            noticias = respuesta.json()["feed"]
            return [
                Noticia(titulo=noticia["title"], resumen=noticia["summary"])
                for noticia in noticias[:limite]
            ]
        except (requests.RequestException, KeyError, TypeError) as error:
            raise ErrorConsultaNoticias(
                "No se pudieron obtener noticias financieras desde Alpha Vantage."
            ) from error
