"""Genera el título y contenido de una alerta a partir de una simulación."""

from abc import ABC, abstractmethod
from decimal import InvalidOperation
import json
import os

import requests

from dominio.excepciones import ErrorConsultaNoticias, ErrorGeneracionAlerta
from dominio.simulacion import Simulacion
from servicios.proveedor_noticias import (
    ProveedorNoticiasAlphaVantage,
    ProveedorNoticiasFinancieras,
)


class GeneradorAlerta(ABC):
    """Contrato: cualquier forma de redactar una alerta debe cumplirlo."""

    @abstractmethod
    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        """Retorna (titulo, contenido)."""
        raise NotImplementedError


class GeneradorAlertaGemini(GeneradorAlerta):
    """Consulta noticias financieras reales y le pide a Gemini que las
    procese para sugerirle una alerta al inversionista.

    A propósito NO se limita a describir el % de rendimiento de la
    simulación (eso sería una "decisión cualitativa genérica"): el contenido
    de la alerta debe reflejar qué está pasando en las noticias del mercado,
    con el resultado de la simulación solo como contexto adicional.
    """

    URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self, proveedor_noticias: ProveedorNoticiasFinancieras | None = None,
        api_key: str | None = None, modelo: str = "gemini-3.8-flash",
    ):
        self._proveedor_noticias = proveedor_noticias or ProveedorNoticiasAlphaVantage()
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._modelo = modelo

    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        if not self._api_key:
            raise ErrorGeneracionAlerta("No se configuró la clave de Gemini.")

        try:
            noticias = self._proveedor_noticias.obtener_noticias()
        except ErrorConsultaNoticias as error:
            raise ErrorGeneracionAlerta(
                "No se pudo generar la alerta: fallaron las noticias financieras."
            ) from error

        texto_noticias = "\n".join(
            f"- {noticia.titulo}: {noticia.resumen}" for noticia in noticias
        ) or "(no hay noticias disponibles en este momento)"

        prompt = (
            "Eres un analista financiero de RiTech SAS, una empresa cuyas "
            "inversiones siguen el índice NASDAQ 100. Estas son las noticias "
            "financieras más recientes relacionadas con el mercado:\n"
            f"{texto_noticias}\n\n"
            "Procesa estas noticias y redacta una alerta breve (máximo dos "
            "frases) que le sugiera al inversionista qué está pasando en el "
            "mercado y qué implica para su inversión — no te limites a "
            "describir el resultado de la simulación. Estos son los datos de "
            "su simulación más reciente, solo como contexto adicional:\n"
            f"- Capital inicial: ${simulacion.capital_inicial:,.0f} COP\n"
            f"- Rendimiento de la inversión: {simulacion.rendimiento_porcentaje}%\n"
            f"- Monto final: ${simulacion.monto_final:,.0f} COP\n"
            "Responde ÚNICAMENTE con un JSON de la forma "
            '{"titulo": "...", "contenido": "..."}.'
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
            datos = json.loads(texto)
            return datos["titulo"], datos["contenido"]
        except (requests.RequestException, KeyError, IndexError, TypeError,
                json.JSONDecodeError, InvalidOperation) as error:
            raise ErrorGeneracionAlerta(
                "No se pudo generar la alerta con Gemini."
            ) from error


class GeneradorAlertaLocal(GeneradorAlerta):
    """Redacta una alerta con reglas locales cuando no hay IA disponible.

    No reemplaza a Gemini: solo garantiza que el inversionista siempre vea
    una lectura del escenario (mercado, riesgo y monto proyectado) aunque
    no se haya configurado ninguna clave.
    """

    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        variacion = simulacion.variacion_nasdaq
        rendimiento = simulacion.rendimiento_porcentaje
        capital = simulacion.capital_inicial
        monto_final = simulacion.monto_final
        diferencia = monto_final - capital

        if rendimiento > 0:
            titulo = "Escenario alcista: el mercado impulsa tu capital"
            contenido = (
                f"El NASDAQ 100 registra una variación de {variacion:.2f}% y la "
                f"regla ×2 de RiTech proyecta un rendimiento de {rendimiento:.2f}%. "
                f"Tu capital pasaría de ${capital:,.0f} a ${monto_final:,.0f} COP "
                f"(ganancia estimada de ${diferencia:,.0f} COP). Una subida fuerte "
                "puede revertirse, así que considera proteger parte de la posición."
            )
        elif rendimiento < 0:
            titulo = "Escenario bajista: conviene revisar el riesgo"
            contenido = (
                f"El NASDAQ 100 cae {abs(variacion):.2f}% y la regla ×2 de RiTech "
                f"amplifica la pérdida a {rendimiento:.2f}%. Tu capital pasaría de "
                f"${capital:,.0f} a ${monto_final:,.0f} COP (pérdida estimada de "
                f"${abs(diferencia):,.0f} COP). Mantener el horizonte de largo plazo "
                "y diversificar reduce el impacto de una jornada negativa."
            )
        else:
            titulo = "Mercado sin cambios: escenario neutro"
            contenido = (
                "El NASDAQ 100 no presenta variación en este momento, por lo que "
                f"tu capital se mantendría en ${capital:,.0f} COP. Es un buen "
                "momento para definir tu perfil de riesgo antes de invertir."
            )
        return titulo, contenido


class GeneradorAlertaConRespaldo(GeneradorAlerta):
    """Intenta la IA y, si no está configurada o falla, usa la alerta local."""

    def __init__(self, primario: GeneradorAlerta, respaldo: GeneradorAlerta):
        self._primario = primario
        self._respaldo = respaldo

    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        try:
            return self._primario.generar(simulacion)
        except ErrorGeneracionAlerta:
            return self._respaldo.generar(simulacion)
