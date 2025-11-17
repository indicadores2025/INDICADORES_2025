import sqlite3

db = sqlite3.connect("database/data.db")
cursor = db.cursor()

# Agregar la columna fecha_termino si no existe
cursor.execute("""
ALTER TABLE preguntas
ADD COLUMN fecha_termino TEXT;
""")

print("✅ Columna 'fecha_termino' agregada correctamente a la tabla 'preguntas'.")
db.commit()
db.close()
