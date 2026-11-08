-- Cuentas predeterminadas de desarrollo. Cambia la contraseña antes de desplegar.
-- Ejecutar con: psql -U <usuario> -d ritech -f db/seed.sql

INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'Laura Benavides',
     'inversionista@ritech.com', 'INVERSIONISTA',
     '$2b$12$EkxtauWYDQ27yi05ceGU1eH/qEm8KZijj2fHyTG3xz3vjMxKHFn0q'),
    ('22222222-2222-2222-2222-222222222222', 'Carlos Ruiz',
     'gestor@ritech.com', 'GESTOR_TI',
     '$2b$12$EkxtauWYDQ27yi05ceGU1eH/qEm8KZijj2fHyTG3xz3vjMxKHFn0q'),
    ('33333333-3333-3333-3333-333333333333', 'Administrador RiTech',
     'admin@ritech.com', 'ADMINISTRADOR',
     '$2b$12$EkxtauWYDQ27yi05ceGU1eH/qEm8KZijj2fHyTG3xz3vjMxKHFn0q')
ON CONFLICT (correo) DO NOTHING;
