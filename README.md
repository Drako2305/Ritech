# RiTech SAS — Backend y panel visual

Software de apoyo a decisiones de inversión para RiTech SAS. Las inversiones
de la empresa dependen del **doble** del comportamiento del índice NASDAQ
100: si el índice sube 2%, RiTech gana 4%; si baja 2%, RiTech pierde 4%.

Proyecto de la asignatura Calidad de Software (UCC) — Sprint 2.

## Contenido del proyecto

- **Backend** (Python + FastAPI + SQLite/PostgreSQL): motor de simulación,
  autenticación, administración de usuarios, operación TI y dashboard.
- **Frontend** (`frontend/`): panel visual en HTML/CSS/JS plano que consume
  la API (login, simular inversión, historial, alertas, panel de
  administración, modo oscuro).

## 1. Requisitos previos

Instalar en el computador donde se vaya a correr el proyecto:

| Herramienta | Versión mínima | Para qué |
|---|---|---|
| [Python](https://www.python.org/downloads/) | 3.11 | Correr el backend |
| [PostgreSQL](https://www.postgresql.org/download/) | 14 | Base de datos opcional para despliegue |
| Un navegador (Chrome, Edge, Firefox) | cualquiera reciente | Usar el panel visual |

No se necesita Node.js ni ningún otro runtime: el frontend es HTML/CSS/JS
puro, sin build ni instalación.

### Claves de API (gratuitas)

La cotización real de QQQ se obtiene de Yahoo Finance sin una clave. Alpha
Vantage puede configurarse como fuente primaria; Gemini habilita las alertas
redactadas por IA. Sin Gemini las simulaciones continúan y se guardan, pero
sin alerta generada por IA.

1. **Alpha Vantage** (variación real del NASDAQ 100 y noticias financieras):
   opcional; al configurarla se usa como fuente primaria de mercado. Crear
   una clave gratis en <https://www.alphavantage.co/support/#api-key>.
2. **Google Gemini** (redacción de las alertas con IA): crear una clave
   gratis en <https://aistudio.google.com/app/apikey>.

## 2. Instalación paso a paso

### 2.1. Copiar el proyecto

Descomprime el `.zip` del proyecto en la carpeta que prefieras, por ejemplo
`Documents/ritech_backend`.

### 2.2. Crear un entorno virtual e instalar las dependencias

Desde una terminal, dentro de la carpeta del proyecto:

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Esto instala las librerías del `requirements.txt`:

- `fastapi` — framework web de la API
- `uvicorn` — servidor que corre la API
- `psycopg[binary]` — driver de PostgreSQL
- `pydantic[email]` — validación de datos (incluye validación de correos)
- `bcrypt` — hasheo seguro de contraseñas
- `requests` — llamadas a Alpha Vantage y Gemini
- `httpx` — usada por las pruebas automatizadas (`TestClient`)
- `pytest` — pruebas automatizadas

### 2.3. Base de datos local o PostgreSQL

Para desarrollo local no es necesario instalar PostgreSQL. Si no se define
`DATABASE_URL`, el backend utiliza SQLite en `db/ritech.db`. Prepara las
cuentas de demostración con:

```powershell
.venv\Scripts\python.exe db\seed_local.py
```

Para usar PostgreSQL en lugar de SQLite:

1. Instala PostgreSQL y anota la contraseña que le pongas al usuario
   `postgres` durante la instalación.
2. Crea la base de datos (con `psql` o con pgAdmin):

   ```sql
   CREATE DATABASE ritech;
   ```

3. Aplica el esquema de tablas:

   ```powershell
   psql -U postgres -d ritech -f db/schema.sql
   ```

4. Carga las cuentas de demostración:

   ```powershell
   psql -U postgres -d ritech -f db/seed.sql
   ```

   Las tres cuentas usan una contraseña de desarrollo común definida en el
   seed; cámbiala antes de desplegar el sistema.

### 2.4. Configurar las variables de entorno

Cada vez que abras una terminal nueva para correr el backend, define:

```powershell
# Windows (PowerShell)
$env:DATABASE_URL = "postgresql://postgres:TU_CONTRASENA@localhost:5432/ritech"
$env:ALPHAVANTAGE_API_KEY = "TU_CLAVE_ALPHAVANTAGE"
$env:GEMINI_API_KEY = "TU_CLAVE_GEMINI"
```

```bash
# Linux / macOS
export DATABASE_URL="postgresql://postgres:TU_CONTRASENA@localhost:5432/ritech"
export ALPHAVANTAGE_API_KEY="TU_CLAVE_ALPHAVANTAGE"
export GEMINI_API_KEY="TU_CLAVE_GEMINI"
```

Si `DATABASE_URL` no se define, se utiliza la base SQLite local. Para
PostgreSQL sí debe definirse la variable con la cadena de conexión.

## 3. Correr el backend

Con el entorno virtual activado y las variables de entorno definidas:

```bash
uvicorn api.main:app --reload
```

Si `uvicorn` no se reconoce como comando (típico en Windows), usa:

```bash
python -m uvicorn api.main:app --reload
```

El backend queda disponible en `http://127.0.0.1:8000`. La documentación
interactiva de la API (Swagger) está en `http://127.0.0.1:8000/docs`.

## 4. Usar el panel visual (frontend)

Con el backend corriendo, abre **`http://127.0.0.1:8000`** en el navegador.
El propio backend sirve el panel visual, así que no hace falta abrir
archivos HTML ni levantar otro servidor.

Flujo típico:

1. **Registrarse** como inversionista. Las cuentas de Gestor TI y
   Administrador son cuentas internas precreadas y no están disponibles en
   el registro público.
2. **Iniciar sesión** con el correo y la contraseña de la cuenta creada.
3. **Inversionista**: simular desde $100.000 COP y consultar su historial.
   El simulador muestra la cotización de QQQ en vivo (Yahoo Finance, sin
   clave) y permite elegir entre la variación real del día o un escenario
   manual de −10% a +10% para ver el efecto de la regla ×2.
4. **Gestor TI**: consultar el estado operativo de la API, base de datos,
   cotizaciones e integración de alertas.
5. **Administración** (solo para `ADMINISTRADOR`):
   dashboard de estadísticas, listar/eliminar usuarios y cambiar roles.
6. El botón de tema en la barra alterna entre modo claro y oscuro.

Cuentas de demostración creadas por el seed de desarrollo (no se muestran en
el login y no deben usarse en producción):

- `inversionista@ritech.com` — Inversionista
- `gestor@ritech.com` — Gestor TI
- `admin@ritech.com` — Administrador

El registro público solo crea cuentas `INVERSIONISTA`; las cuentas internas se
crean por seed y no se pueden seleccionar al registrarse.

## 5. Ejecutar las pruebas automatizadas

```bash
# Pruebas unitarias (no requieren base de datos)
pytest

# Pruebas de integración (requieren PostgreSQL corriendo con el esquema aplicado)
pytest -m integracion
```

## 6. Estructura del proyecto

```
ritech_backend/
├── api/            # FastAPI: rutas (main.py), esquemas y dependencias
├── dominio/        # Entidades y excepciones del negocio
├── servicios/      # Lógica de negocio (motor de simulación, autenticación,
│                   # administración de usuarios, alertas, dashboard)
├── db/             # schema.sql y seed.sql
├── frontend/       # Panel visual (HTML/CSS/JS)
├── tests/          # Pruebas unitarias y de integración
├── requirements.txt
├── pytest.ini
└── conftest.py
```

## 7. Limitaciones conocidas

- El login no emite un token de sesión: la "sesión" del panel visual es solo
  una conveniencia guardada en el navegador (`sessionStorage`), y los
  endpoints de administración/dashboard verifican el rol consultando el
  `id_usuario_solicitante` que se les pasa. Esto es suficientemente seguro
  para el alcance académico del proyecto, pero no evita que alguien con
  acceso a la consola del navegador falsifique ese id.
- Alpha Vantage (capa gratuita) tiene un límite de 25 solicitudes diarias
  por clave.
- La variación del NASDAQ 100 se obtiene del ETF `QQQ` como proxy, ya que
  el índice como tal suele requerir un plan de pago en Alpha Vantage.
- Si no hay clave de Gemini, las alertas se redactan con reglas locales
  (`GeneradorAlertaLocal`), de modo que el simulador siempre muestra una
  lectura del escenario. Gemini sigue siendo opcional.
- Para PostgreSQL, define `DATABASE_URL` y aplica `db/schema.sql` y
  `db/seed.sql`. Sin `DATABASE_URL`, la demo funciona con SQLite local.
