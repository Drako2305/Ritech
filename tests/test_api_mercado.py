from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from api.dependencias import obtener_proveedor_mercado
from api.main import app
from servicios.proveedor_mercado import Cotizacion, PuntoMercado


class ProveedorMercadoFalso:
    def __init__(self):
        self.llamadas = 0

    def obtener_cotizacion(self) -> Cotizacion:
        self.llamadas += 1
        return Cotizacion(
            simbolo="QQQ",
            nombre="Invesco QQQ · NASDAQ 100",
            precio=Decimal("500.25"),
            cierre_anterior=Decimal("495.00"),
            variacion_absoluta=Decimal("5.25"),
            variacion_porcentaje=Decimal("1.06"),
            moneda="USD",
            maximo_dia=Decimal("501.00"),
            minimo_dia=Decimal("494.50"),
            actualizado_en=datetime(2026, 11, 7, 15, 30),
            historial=[
                PuntoMercado(fecha=datetime(2026, 11, 6), cierre=Decimal("495.00")),
                PuntoMercado(fecha=datetime(2026, 11, 7), cierre=Decimal("500.25")),
            ],
        )


def test_devuelve_la_cotizacion_de_mercado():
    proveedor = ProveedorMercadoFalso()
    app.dependency_overrides[obtener_proveedor_mercado] = lambda: proveedor
    client = TestClient(app)

    respuesta = client.get("/mercado/cotizacion")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["simbolo"] == "QQQ"
    assert Decimal(cuerpo["precio"]) == Decimal("500.25")
    assert Decimal(cuerpo["variacion_porcentaje"]) == Decimal("1.06")
    assert len(cuerpo["historial"]) == 2

    app.dependency_overrides.clear()
