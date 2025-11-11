import sqlite3, os

# Crear carpeta "database" si no existe
if not os.path.exists("database"):
    os.makedirs("database")

# Conexión a la base de datos
conn = sqlite3.connect("database/data.db")
cur = conn.cursor()

# ---------- TABLA UNIDAD ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS unidad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    activo INTEGER DEFAULT 1
)
""")

# ---------- TABLA USUARIOS ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contrasena TEXT NOT NULL,
    tipo TEXT DEFAULT 'usuario',
    unidad_id INTEGER,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (unidad_id) REFERENCES unidad (id)
)
""")

# ---------- TABLA PRESUPUESTO ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS presupuesto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    periodo TEXT,
    monto_total REAL DEFAULT 0,
    activo INTEGER DEFAULT 1
)
""")

# ---------- TABLA PERIODO ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS periodo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes TEXT,
    año INTEGER,
    abierto INTEGER DEFAULT 0
)
""")

# ---------- TABLA PREGUNTAS ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS preguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT NOT NULL,
    tipo TEXT,
    presupuesto_id INTEGER,
    unidad_id INTEGER,
    usuario_id INTEGER,
    afecta_presupuesto INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (presupuesto_id) REFERENCES presupuesto (id),
    FOREIGN KEY (unidad_id) REFERENCES unidad (id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
""")

# ---------- TABLA RESPUESTAS ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS respuestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pregunta_id INTEGER,
    usuario_id INTEGER,
    valor TEXT,
    mes TEXT,
    año INTEGER,
    fecha_ingreso TEXT,
    FOREIGN KEY (pregunta_id) REFERENCES preguntas (id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
""")

# ---------- USUARIO ADMIN INICIAL ----------
cur.execute("""
INSERT OR IGNORE INTO usuarios (id, nombre, contrasena, tipo, activo)
VALUES (1, 'admin', '1234', 'admin', 1)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada correctamente en /database/data.db")
print("Usuario administrador inicial:")
print("Usuario: admin")
print("Contraseña: 1234")
