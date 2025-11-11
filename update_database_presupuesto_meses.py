import sqlite3

conn = sqlite3.connect("database/data.db")
cur = conn.cursor()

# Crear tabla nueva para meses y años asociados al presupuesto
cur.execute("""
CREATE TABLE IF NOT EXISTS presupuesto_meses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id INTEGER,
    mes TEXT,
    año INTEGER,
    FOREIGN KEY (presupuesto_id) REFERENCES presupuesto(id)
)
""")

conn.commit()
conn.close()

print("✅ Tabla 'presupuesto_meses' creada o actualizada correctamente.")
