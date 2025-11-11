import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash

presupuesto_bp = Blueprint('presupuesto', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================
# PANEL DE GESTIÓN DE PRESUPUESTOS
# ============================================
@presupuesto_bp.route("/presupuesto", methods=["GET", "POST"])
def presupuesto():
    db = get_db()

    if request.method == "POST":
        nombre = request.form["nombre"]
        monto = float(request.form["monto_total"])
        meses = request.form.getlist("meses")
        años = request.form.getlist("años")

        db.execute("INSERT INTO presupuesto (nombre, monto_total, activo) VALUES (?, ?, 1)", (nombre, monto))
        db.commit()

        presupuesto_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        for m in meses:
            for a in años:
                db.execute("INSERT INTO presupuesto_meses (presupuesto_id, mes, año) VALUES (?, ?, ?)", (presupuesto_id, m, a))
        db.commit()

        flash("✅ Presupuesto creado correctamente con meses y años asociados.", "success")
        return redirect(url_for("presupuesto.presupuesto"))

    # Listar presupuestos con su ejecución mensual correcta
    presupuestos_db = db.execute("SELECT id, nombre, monto_total, activo FROM presupuesto ORDER BY id DESC").fetchall()
    data_presupuestos = []

    for p in presupuestos_db:
        meses_asoc = db.execute("SELECT mes, año FROM presupuesto_meses WHERE presupuesto_id=?", (p["id"],)).fetchall()
        lista_meses = [f"{m['mes']} {m['año']}" for m in meses_asoc]

        # 🔸 Cálculo: solo descuenta las respuestas cuyos mes y año coincidan con presupuesto_meses
        ejecutado = db.execute("""
            SELECT SUM(CAST(r.valor AS FLOAT)) AS total
            FROM respuestas r
            JOIN preguntas q ON q.id = r.pregunta_id
            JOIN presupuesto_meses pm ON pm.presupuesto_id = q.presupuesto_id
            WHERE q.presupuesto_id = ?
            AND q.afecta_presupuesto = 1
            AND r.mes = pm.mes
            AND r.año = pm.año
        """, (p["id"],)).fetchone()["total"] or 0

        restante = (p["monto_total"] or 0) - ejecutado
        porcentaje = (ejecutado / p["monto_total"] * 100) if p["monto_total"] > 0 else 0

        data_presupuestos.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "monto_total": p["monto_total"],
            "meses": ", ".join(lista_meses) if lista_meses else "Sin asignar",
            "ejecutado": ejecutado,
            "restante": restante,
            "porcentaje": porcentaje,
        })

    return render_template("presupuesto.html", presupuestos=data_presupuestos)

# ============================================
# RESUMEN GLOBAL DEL SISTEMA
# ============================================
def calcular_resumen_presupuesto():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    presupuestos = db.execute("SELECT id, nombre, monto_total FROM presupuesto WHERE activo=1").fetchall()
    data = []
    total_presupuesto = 0
    total_ejecutado = 0

    for p in presupuestos:
        ejecutado = db.execute("""
            SELECT SUM(CAST(r.valor AS FLOAT)) AS total
            FROM respuestas r
            JOIN preguntas q ON q.id = r.pregunta_id
            JOIN presupuesto_meses pm ON pm.presupuesto_id = q.presupuesto_id
            WHERE q.presupuesto_id = ?
            AND q.afecta_presupuesto = 1
            AND r.mes = pm.mes
            AND r.año = pm.año
        """, (p["id"],)).fetchone()["total"] or 0

        restante = (p["monto_total"] or 0) - ejecutado
        porcentaje = (ejecutado / p["monto_total"] * 100) if p["monto_total"] > 0 else 0

        total_presupuesto += p["monto_total"]
        total_ejecutado += ejecutado

        data.append({
            "nombre": p["nombre"],
            "monto_total": p["monto_total"],
            "ejecutado": ejecutado,
            "restante": restante,
            "porcentaje": porcentaje
        })

    total_restante = total_presupuesto - total_ejecutado
    total_porcentaje = (total_ejecutado / total_presupuesto * 100) if total_presupuesto > 0 else 0

    conn.close()

    return {
        "total": total_presupuesto,
        "ejecutado": total_ejecutado,
        "restante": total_restante,
        "porcentaje": total_porcentaje,
        "detalle": data
    }
