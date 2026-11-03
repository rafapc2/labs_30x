CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    proveedor TEXT NOT NULL CHECK (proveedor IN ('google', 'github')),
    id_proveedor TEXT NOT NULL,
    nombre TEXT NOT NULL,
    creado TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (proveedor, id_proveedor)
);

CREATE TABLE apps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    descripcion_larga TEXT NOT NULL DEFAULT '',
    categoria TEXT NOT NULL DEFAULT '',
    contacto JSONB NOT NULL DEFAULT '{}'::jsonb,
    estado TEXT NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador', 'desplegada', 'retirada')),
    verificada BOOLEAN NOT NULL DEFAULT FALSE,
    token_verificacion TEXT NOT NULL,
    creado TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX apps_usuario_creado ON apps (usuario_id, creado);

CREATE TABLE contenido (
    id SERIAL PRIMARY KEY,
    app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    titulo TEXT NOT NULL DEFAULT '',
    texto TEXT NOT NULL DEFAULT '',
    tsv TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('spanish', coalesce(titulo, '') || ' ' || coalesce(texto, ''))
    ) STORED
);
CREATE INDEX contenido_tsv ON contenido USING GIN (tsv);
CREATE INDEX contenido_app ON contenido (app_id);

CREATE TABLE herramientas (
    id SERIAL PRIMARY KEY,
    app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'lectura',
    UNIQUE (app_id, nombre)
);

-- BR-MCP-05: no existe ninguna columna para el texto de la consulta.
CREATE TABLE llamadas (
    id BIGSERIAL PRIMARY KEY,
    app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    herramienta TEXT NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
    resultado TEXT NOT NULL CHECK (resultado IN ('ok', 'error'))
);
CREATE INDEX llamadas_app_fecha ON llamadas (app_id, fecha);

-- Cuenta mensajes del simulador por cuenta para el límite por hora (S13). Sin texto.
CREATE TABLE uso_simulador (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX uso_simulador_usuario_fecha ON uso_simulador (usuario_id, fecha);
