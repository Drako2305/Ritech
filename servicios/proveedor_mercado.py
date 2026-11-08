"""Cotizaciones de mercado para el panel del simulador.

A diferencia de GeneradorVariacionNasdaq (que solo devuelve el porcentaje
del día), este proveedor entrega una foto completa del instrumento: precio,
variación, rango del día y el histórico reciente para dibujar la gráfica.

La fuente por defecto es Yahoo Finance (sin clave) usando el ETF QQQ como
proxy del NASDAQ 100, igual que el resto del proyecto.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

import requests

from dominio.excepciones import ErrorGeneracionVariacion


@dataclass(frozen=True)
class PuntoMercado:
    fecha: datetime
    cierre: Decimal


@dataclass(frozen=True)
class Cotizacion:
    simbolo: str
    nombre: str
    precio: Decimal
    cierre_anterior: Decimal
    variacion_absoluta: Decimal
    variacion_porcentaje: Decimal
    moneda: str
    maximo_dia: Decimal | None
    minimo_dia: Decimal | None
    actualizado_en: datetime
    historial: list[PuntoMercado]


class ProveedorMercadoYahoo:
    """Obtiene la cotización de QQQ desde Yahoo Finance."""

    URL_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
    NOMBRES = {
        "QQQ": "Invesco QQQ · NASDAQ 100",
        "^NDX": "NASDAQ 100",
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corp.",
        "NVDA": "NVIDIA Corp.",
        "AMZN": "Amazon.com",
        "TSLA": "Tesla Inc.",
        "GOOGL": "Alphabet Inc.",
        "META": "Meta Platforms",
    }

    def __init__(self, simbolo: str = "QQQ"):
        self._simbolo = simbolo

    def obtener_cotizacion(self) -> Cotizacion:
        try:
            respuesta = requests.get(
                f"{self.URL_BASE}/{self._simbolo}",
                params={"range": "1mo", "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0 RiTech/1.0"},
                timeout=12,
            )
            respuesta.raise_for_status()
            resultado = respuesta.json()["chart"]["result"][0]
            meta = resultado["meta"]

            precio = Decimal(str(meta["regularMarketPrice"]))

            # Yahoo no siempre envía regularMarketChange. Si envía el
            # porcentaje, se reconstruye el cierre anterior a partir de él;
            # de lo contrario se usan los campos de cierre disponibles.
            cambio_pct = meta.get("regularMarketChangePercent")
            if cambio_pct is not None:
                cambio_pct = Decimal(str(cambio_pct))
                factor = Decimal("1") + cambio_pct / Decimal("100")
                cierre_anterior = precio / factor if factor != 0 else precio
                cambio_absoluto = precio - cierre_anterior
            else:
                cierre_anterior = Decimal(
                    str(
                        meta.get("previousClose")
                        or meta.get("chartPreviousClose")
                        or precio
                    )
                )
                cambio_absoluto = precio - cierre_anterior
                cambio_pct = (
                    cambio_absoluto / cierre_anterior * Decimal("100")
                    if cierre_anterior
                    else Decimal("0")
                )

            if not precio.is_finite() or not cambio_pct.is_finite():
                raise ValueError("Cotización no válida.")

            marcas = resultado.get("timestamp") or []
            cierres = (
                resultado.get("indicators", {}).get("quote", [{}])[0].get("close") or []
            )
            historial = [
                PuntoMercado(fecha=datetime.fromtimestamp(marca), cierre=Decimal(str(cierre)))
                for marca, cierre in zip(marcas, cierres)
                if cierre is not None
            ]

            marca_actual = meta.get("regularMarketTime")
            actualizado_en = (
                datetime.fromtimestamp(marca_actual)
                if marca_actual
                else datetime.now()
            )

            maximo = meta.get("regularMarketDayHigh")
            minimo = meta.get("regularMarketDayLow")

            return Cotizacion(
                simbolo=str(meta.get("symbol") or self._simbolo),
                nombre=self.NOMBRES.get(self._simbolo, self._simbolo),
                precio=precio,
                cierre_anterior=cierre_anterior,
                variacion_absoluta=cambio_absoluto,
                variacion_porcentaje=cambio_pct,
                moneda=str(meta.get("currency") or "USD"),
                maximo_dia=Decimal(str(maximo)) if maximo is not None else None,
                minimo_dia=Decimal(str(minimo)) if minimo is not None else None,
                actualizado_en=actualizado_en,
                historial=historial,
            )
        except (
            requests.RequestException,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            InvalidOperation,
        ) as error:
            raise ErrorGeneracionVariacion(
                "No se pudo obtener la cotización de mercado desde Yahoo Finance."
            ) from error
