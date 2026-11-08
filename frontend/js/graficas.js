const Graficas = (() => {
  function preparar(idCanvas) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas) return null;
    const ancho = Math.max(canvas.clientWidth, 320);
    const alto = Math.max(canvas.clientHeight, 160);
    const escala = window.devicePixelRatio || 1;
    canvas.width = ancho * escala;
    canvas.height = alto * escala;
    const contexto = canvas.getContext("2d");
    contexto.setTransform(escala, 0, 0, escala, 0, 0);
    contexto.clearRect(0, 0, ancho, alto);
    return { contexto, ancho, alto };
  }

  function dibujarGuia(contexto, ancho, alto, margen) {
    contexto.strokeStyle = "rgba(28, 55, 53, 0.10)";
    contexto.lineWidth = 1;
    for (let indice = 0; indice < 4; indice += 1) {
      const y = margen.superior + ((alto - margen.superior - margen.inferior) / 3) * indice;
      contexto.beginPath();
      contexto.moveTo(margen.izquierdo, y);
      contexto.lineTo(ancho - margen.derecho, y);
      contexto.stroke();
    }
  }

  function barras(idCanvas, datos, opciones = {}) {
    const lienzo = preparar(idCanvas);
    if (!lienzo || !datos.length) return;
    const { contexto, ancho, alto } = lienzo;
    const margen = { superior: 18, inferior: 48, izquierdo: 12, derecho: 12 };
    dibujarGuia(contexto, ancho, alto, margen);

    const maximo = Math.max(...datos.map((dato) => dato.valor), 1) * 1.18;
    const area = alto - margen.superior - margen.inferior;
    const espacio = (ancho - margen.izquierdo - margen.derecho) / datos.length;
    const anchoBarra = Math.min(88, espacio * 0.46);

    datos.forEach((dato, indice) => {
      const x = margen.izquierdo + espacio * indice + (espacio - anchoBarra) / 2;
      const altoBarra = Math.max(4, (dato.valor / maximo) * area);
      const y = alto - margen.inferior - altoBarra;
      contexto.fillStyle = dato.color || "#13866f";
      contexto.beginPath();
      contexto.roundRect(x, y, anchoBarra, altoBarra, [7, 7, 2, 2]);
      contexto.fill();
      contexto.fillStyle = "#263b39";
      contexto.font = "600 12px Segoe UI, sans-serif";
      contexto.textAlign = "center";
      contexto.fillText(opciones.formato ? opciones.formato(dato.valor) : String(dato.valor), x + anchoBarra / 2, y - 9);
      contexto.fillStyle = "#71817d";
      contexto.font = "11px Segoe UI, sans-serif";
      contexto.fillText(dato.etiqueta, x + anchoBarra / 2, alto - 17, espacio - 8);
    });
  }

  function linea(idCanvas, datos, opciones = {}) {
    const lienzo = preparar(idCanvas);
    if (!lienzo || !datos.length) return;
    const { contexto, ancho, alto } = lienzo;
    const margen = { superior: 22, inferior: 48, izquierdo: 16, derecho: 16 };
    dibujarGuia(contexto, ancho, alto, margen);

    const valores = datos.map((dato) => dato.valor);
    const rango = Math.max(...valores) - Math.min(...valores);
    const relleno = Math.max(rango * 0.18, Math.abs(Math.max(...valores)) * 0.03, 1);
    const minimo = Math.min(...valores) - relleno;
    const maximo = Math.max(...valores) + relleno;
    const altoUtil = alto - margen.superior - margen.inferior;
    const anchoUtil = ancho - margen.izquierdo - margen.derecho;
    const puntos = datos.map((dato, indice) => ({
      x: margen.izquierdo + (datos.length === 1 ? anchoUtil / 2 : (anchoUtil * indice) / (datos.length - 1)),
      y: margen.superior + ((maximo - dato.valor) / (maximo - minimo || 1)) * altoUtil,
      etiqueta: dato.etiqueta,
    }));

    const color = opciones.color || "#1d4ed8";
    const area = contexto.createLinearGradient(0, margen.superior, 0, alto - margen.inferior);
    area.addColorStop(0, opciones.areaColor || "rgba(29, 78, 216, 0.2)");
    area.addColorStop(1, "rgba(29, 78, 216, 0.01)");
    contexto.beginPath();
    contexto.moveTo(puntos[0].x, alto - margen.inferior);
    puntos.forEach((punto) => contexto.lineTo(punto.x, punto.y));
    contexto.lineTo(puntos[puntos.length - 1].x, alto - margen.inferior);
    contexto.closePath();
    contexto.fillStyle = area;
    contexto.fill();

    contexto.beginPath();
    puntos.forEach((punto, indice) => {
      if (indice === 0) contexto.moveTo(punto.x, punto.y);
      else contexto.lineTo(punto.x, punto.y);
    });
    contexto.strokeStyle = color;
    contexto.lineWidth = 3;
    contexto.lineJoin = "round";
    contexto.lineCap = "round";
    contexto.stroke();

    puntos.forEach((punto, indice) => {
      contexto.beginPath();
      contexto.arc(punto.x, punto.y, indice === puntos.length - 1 ? 5 : 3.5, 0, Math.PI * 2);
      contexto.fillStyle = indice === puntos.length - 1 ? "#d2a84d" : color;
      contexto.fill();
      if (opciones.etiquetas !== false) {
        contexto.fillStyle = "#71817d";
        contexto.font = "11px Segoe UI, sans-serif";
        contexto.textAlign = indice === 0 ? "left" : indice === puntos.length - 1 ? "right" : "center";
        contexto.fillText(punto.etiqueta, punto.x, alto - 17);
      }
    });

    if (opciones.valorFinal) {
      const ultimo = puntos[puntos.length - 1];
      contexto.fillStyle = "#263b39";
      contexto.font = "700 12px Segoe UI, sans-serif";
      contexto.textAlign = "right";
      contexto.fillText(opciones.valorFinal, ultimo.x, ultimo.y - 12);
    }
  }

  function sparkline(idCanvas, datos, opciones = {}) {
    const lienzo = preparar(idCanvas);
    if (!lienzo || datos.length < 2) return;
    const { contexto, ancho, alto } = lienzo;
    const valores = datos.map((dato) => Number(dato.valor));
    const minimo = Math.min(...valores);
    const maximo = Math.max(...valores);
    const margen = 10;
    const rango = maximo - minimo || 1;
    const puntos = valores.map((valor, indice) => ({
      x: margen + ((ancho - margen * 2) * indice) / (valores.length - 1),
      y: margen + ((maximo - valor) / rango) * (alto - margen * 2),
    }));

    const color = opciones.color || "#60d7a3";
    const gradiente = contexto.createLinearGradient(0, 0, 0, alto);
    gradiente.addColorStop(0, opciones.areaColor || "rgba(96, 215, 163, 0.35)");
    gradiente.addColorStop(1, "rgba(96, 215, 163, 0)");
    contexto.beginPath();
    contexto.moveTo(puntos[0].x, alto);
    puntos.forEach((punto) => contexto.lineTo(punto.x, punto.y));
    contexto.lineTo(puntos[puntos.length - 1].x, alto);
    contexto.closePath();
    contexto.fillStyle = gradiente;
    contexto.fill();

    contexto.beginPath();
    puntos.forEach((punto, indice) => {
      if (indice === 0) contexto.moveTo(punto.x, punto.y);
      else contexto.lineTo(punto.x, punto.y);
    });
    contexto.strokeStyle = color;
    contexto.lineWidth = 2.5;
    contexto.lineJoin = "round";
    contexto.lineCap = "round";
    contexto.stroke();
  }

  return { barras, linea, sparkline };
})();
