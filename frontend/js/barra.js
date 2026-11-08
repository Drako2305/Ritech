/** Barra de navegación compartida entre las páginas ya logueadas. */
function renderizarBarra(idContenedor, paginaActual) {
  const usuario = SesionUsuario.obtener();
  const contenedor = document.getElementById(idContenedor);
  if (!usuario || !contenedor) return;

  const enlace = (href, etiqueta, clave) =>
    `<a href="${href}" class="${paginaActual === clave ? "activo" : ""}">${etiqueta}</a>`;
  const paginaPorRol = {
    INVERSIONISTA: [
      enlace("simular.html", "Simular", "simular"),
      enlace("historial.html", "Historial", "historial"),
    ],
    GESTOR_TI: [enlace("operacion.html", "Operación TI", "operacion")],
    ADMINISTRADOR: [enlace("admin.html", "Administración", "admin")],
  };

  contenedor.innerHTML = `
    <nav class="barra">
      <div class="marca">RiTech <span class="etiqueta-rol">${usuario.rol}</span></div>
      <div class="enlaces">
        ${(paginaPorRol[usuario.rol] || []).join("")}
      </div>
      <div class="acciones">
        <span class="nombre-usuario">${usuario.nombre}</span>
        <button id="boton-tema" class="boton-icono" type="button" aria-label="Cambiar tema"></button>
        <button id="boton-salir" class="boton-secundario">Salir</button>
      </div>
    </nav>`;

  document.getElementById("boton-tema").addEventListener("click", () => GestorTema.alternar());
  GestorTema.actualizarControl();
  document.getElementById("boton-salir").addEventListener("click", () => {
    SesionUsuario.cerrar();
    window.location.href = "index.html";
  });
}
