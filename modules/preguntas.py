import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash

preguntas_bp = Blueprint('preguntas', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@preguntas_bp.route("/preguntas", methods=["GET", "POST"])
def preguntas():
    db = get_db()
    presupuestos = db.execute("SELECT * FROM presupuesto WHERE activo=1").fetchall()
    unidades = db.execute("SELECT * FROM unidad WHERE activo=1").fetchall()
    usuarios = db.execute("SELECT * FROM usuarios WHERE activo=1").fetchall()

    if request.method == "POST":
        texto = request.form["texto"]
        tipo = request.form["tipo"]
        presupuesto_id = request.form["presupuesto_id"]
        unidad_id = request.form["unidad_id"]
        usuario_id = request.form["usuario_id"]
        afecta = 1 if "afecta_presupuesto" in request.form else 0

        db.execute("""
        INSERT INTO preguntas (texto, tipo, presupuesto_id, unidad_id, usuario_id, afecta_presupuesto, activo)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (texto, tipo, presupuesto_id, unidad_id, usuario_id, afecta))
        db.commit()
        flash("📝 Pregunta agregada correctamente", "success")
        return redirect(url_for("preguntas.preguntas"))

    preguntas = db.execute("""
    SELECT p.id, p.texto, p.tipo, p.activo,
           pr.nombre AS presupuesto, u.nombre AS unidad, us.nombre AS usuario,
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

@preguntas_bp.route("/preguntas/editar/<int:id>", methods=["GET", "POST"])
def editar_pregunta(id):
    db = get_db()
    if request.method == "POST":
        texto = request.form["texto"]
        tipo = request.form["tipo"]
        presupuesto_id = request.form["presupuesto_id"]
        unidad_id = request.form["unidad_id"]
        usuario_id = request.form["usuario_id"]
        afecta = 1 if "afecta_presupuesto" in request.form else 0

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

@preguntas_bp.route("/preguntas/desactivar/<int:id>")
def desactivar_pregunta(id):
    db = get_db()
    pregunta = db.execute("SELECT activo FROM preguntas WHERE id=?", (id,)).fetchone()
    nuevo_estado = 0 if pregunta["activo"] == 1 else 1
    db.execute("UPDATE preguntas SET activo=? WHERE id=?", (nuevo_estado, id))
    db.commit()
    flash("⚙️ Estado de la pregunta actualizado", "info")
    return redirect(url_for("preguntas.preguntas"))
