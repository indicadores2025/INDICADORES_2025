import sqlite3
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import io

preguntas_bp = Blueprint('preguntas', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# 🟠 LISTAR Y CREAR PREGUNTAS
@preguntas_bp.route("/preguntas", methods=["GET", "POST"])
def preguntas():
    db = get_db()
    presupuestos = db.execute("SELECT * FROM presupuesto WHERE activo=1").fetchall()
    unidades = db.execute("SELECT * FROM unidad WHERE activo=1").fetchall()
    usuarios = db.execute("SELECT * FROM usuarios WHERE activo=1").fetchall()

    if request.method == "POST":
        texto = request.form["texto"]
        tipo = request.form["tipo"]
        unidad_id = request.form["unidad_id"]
        usuario_id = request.form["usuario_id"]
        afecta = 1 if "afecta_presupuesto" in request.form else 0
        presupuesto_id = request.form.get("presupuesto_id") if afecta == 1 and request.form.get("presupuesto_id") else None

        db.execute("""
        INSERT INTO preguntas (texto, tipo, presupuesto_id, unidad_id, usuario_id, afecta_presupuesto, activo)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (texto, tipo, presupuesto_id, unidad_id, usuario_id, afecta))
        db.commit()
        flash("📝 Pregunta agregada correctamente", "success")
        return redirect(url_for("preguntas.preguntas"))

    preguntas = db.execute("""
    SELECT p.id, p.texto, p.tipo, p.activo,
           COALESCE(pr.nombre, 'No aplica') AS presupuesto,
           u.nombre AS unidad, us.nombre AS usuario,
           p.afecta_presupuesto
    FROM preguntas p
    LEFT JOIN presupuesto pr ON p.presupuesto_id = pr.id
    LEFT JOIN unidad u ON p.unidad_id = u.id
    LEFT JOIN usuarios us ON p.usuario_id = us.id
    ORDER BY p.id DESC
    """).fetchall()

    return render_template("preguntas.html",
                           preguntas=preguntas,
                           presupuestos=presupuestos,
                           unidades=unidades,
                           usuarios=usuarios)


# 🟢 EDITAR PREGUNTA
@preguntas_bp.route("/preguntas/editar/<int:id>", methods=["GET", "POST"])
def editar_pregunta(id):
    db = get_db()

    if request.method == "POST":
        texto = request.form["texto"]
        tipo = request.form["tipo"]
        unidad_id = request.form["unidad_id"]
        usuario_id = request.form["usuario_id"]
        afecta = 1 if "afecta_presupuesto" in request.form else 0
        presupuesto_id = request.form.get("presupuesto_id") if afecta == 1 and request.form.get("presupuesto_id") else None

        db.execute("""
        UPDATE preguntas
        SET texto=?, tipo=?, presupuesto_id=?, unidad_id=?, usuario_id=?, afecta_presupuesto=?
        WHERE id=?
        """, (texto, tipo, presupuesto_id, unidad_id, usuario_id, afecta, id))
        db.commit()
        flash("✏️ Pregunta actualizada correctamente", "success")
        return redirect(url_for("preguntas.preguntas"))

    pregunta = db.execute("SELECT * FROM preguntas WHERE id=?", (id,)).fetchone()
    presupuestos = db.execute("SELECT * FROM presupuesto WHERE activo=1").fetchall()
    unidades = db.execute("SELECT * FROM unidad WHERE activo=1").fetchall()
    usuarios = db.execute("SELECT * FROM usuarios WHERE activo=1").fetchall()

    return render_template("editar_pregunta.html",
                           pregunta=pregunta,
                           presupuestos=presupuestos,
                           unidades=unidades,
                           usuarios=usuarios)


# 🔴 ELIMINAR PREGUNTA
@preguntas_bp.route("/preguntas/eliminar/<int:id>", methods=["GET"])
def eliminar_pregunta(id):
    db = get_db()
    db.execute("DELETE FROM preguntas WHERE id=?", (id,))
    db.commit()
    flash("🗑️ Pregunta eliminada permanentemente", "danger")
    return redirect(url_for("preguntas.preguntas"))


# 📄 EXPORTAR TODAS LAS PREGUNTAS A EXCEL
@preguntas_bp.route("/preguntas/exportar_excel")
def exportar_excel():
    db = get_db()
    df = pd.read_sql_query("""
        SELECT p.id AS ID, p.texto AS Pregunta, p.tipo AS Tipo,
               COALESCE(pr.nombre, 'No aplica') AS Presupuesto,
               u.nombre AS Unidad, us.nombre AS Usuario,
               CASE p.afecta_presupuesto WHEN 1 THEN 'Sí' ELSE 'No' END AS AfectaPresupuesto,
               CASE p.activo WHEN 1 THEN 'Sí' ELSE 'No' END AS Activo
        FROM preguntas p
        LEFT JOIN presupuesto pr ON p.presupuesto_id = pr.id
        LEFT JOIN unidad u ON p.unidad_id = u.id
        LEFT JOIN usuarios us ON p.usuario_id = us.id
        ORDER BY p.id DESC
    """, db)

    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name="Preguntas")
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="preguntas_exportadas.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# 📥 DESCARGAR PLANTILLA DE EJEMPLO
@preguntas_bp.route("/preguntas/descargar_ejemplo")
def descargar_ejemplo():
    data = {
        "texto": ["Ejemplo: Porcentaje de satisfacción usuaria"],
        "tipo": ["Porcentaje"],
        "unidad": ["Calidad"],
        "usuario": ["Ana"],
        "afecta_presupuesto": [1],
        "presupuesto": ["Presupuesto General"]
    }

    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name="Plantilla")
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="plantilla_preguntas.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# 📤 IMPORTAR PREGUNTAS DESDE EXCEL
@preguntas_bp.route("/preguntas/importar_excel", methods=["POST"])
def importar_excel():
    if "archivo" not in request.files:
        flash("⚠️ No se seleccionó ningún archivo.", "error")
        return redirect(url_for("preguntas.preguntas"))

    archivo = request.files["archivo"]
    if archivo.filename == "":
        flash("⚠️ Archivo no válido.", "error")
        return redirect(url_for("preguntas.preguntas"))

    try:
        df = pd.read_excel(archivo)
        db = get_db()

        for _, row in df.iterrows():
            texto = str(row.get("texto", "")).strip()
            tipo = str(row.get("tipo", "Texto")).strip()
            unidad = str(row.get("unidad", "")).strip()
            usuario = str(row.get("usuario", "")).strip()
            afecta = int(row.get("afecta_presupuesto", 0))
            presupuesto_nombre = str(row.get("presupuesto", "")).strip() if afecta == 1 else None

            unidad_id = db.execute("SELECT id FROM unidad WHERE nombre=?", (unidad,)).fetchone()
            usuario_id = db.execute("SELECT id FROM usuarios WHERE nombre=?", (usuario,)).fetchone()
            presupuesto_id = None

            if afecta == 1 and presupuesto_nombre:
                pres = db.execute("SELECT id FROM presupuesto WHERE nombre=?", (presupuesto_nombre,)).fetchone()
                if pres:
                    presupuesto_id = pres["id"]

            if unidad_id and usuario_id and texto:
                db.execute("""
                    INSERT INTO preguntas (texto, tipo, presupuesto_id, unidad_id, usuario_id, afecta_presupuesto, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (texto, tipo, presupuesto_id, unidad_id["id"], usuario_id["id"], afecta))

        db.commit()
        flash("✅ Preguntas importadas correctamente.", "success")

    except Exception as e:
        flash(f"❌ Error al importar: {str(e)}", "error")

    return redirect(url_for("preguntas.preguntas"))
