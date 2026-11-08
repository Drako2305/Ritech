-- Esquema RiTech: usuarios, simulaciones y noticias/alertas (Sprint 2).
-- Ejecutar con: psql -U <usuario> -d ritech -f db/schema.sql

CREATE TABLE IF NOT EXISTS usuarios (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre        VARCHAR(120) NOT NULL,
    correo        VARCHAR(150) NOT NULL UNIQUE,
    rol           VARCHAR(20) NOT NULL
                      CHECK (rol IN ('INVERSIONISTA', 'GESTOR_TI', 'ADMINISTRADOR')),
    contrasena_hash VARCHAR(60) NOT NULL,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS simulaciones (
    id                      UUID PRIMARY KEY,
    id_usuario              UUID NOT NULL REFERENCES usuarios (id),
    capital_inicial         NUMERIC(18, 2) NOT NULL CHECK (capital_inicial > 0),
    variacion_nasdaq        NUMERIC(10, 4) NOT NULL,
    rendimiento_porcentaje  NUMERIC(10, 4) NOT NULL,
    monto_final             NUMERIC(18, 2) NOT NULL,
    fecha_simulacion        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_simulaciones_usuario ON simulaciones (id_usuario);

CREATE TABLE IF NOT EXISTS noticias_alertas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_simulacion   UUID NOT NULL REFERENCES simulaciones (id),
    titulo          VARCHAR(200) NOT NULL,
    contenido       TEXT NOT NULL,
    generado_por_ia BOOLEAN NOT NULL DEFAULT true,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alertas_simulacion ON noticias_alertas (id_simulacion);
