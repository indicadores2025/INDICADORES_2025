import sqlite3
import pandas as pd
import datetime
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file

auditoria_bp = Blueprint('auditoria', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================
# PANEL DE AUDITORÍA ADMINISTRADOR
# ======================================
@auditoria_bp.route("/auditoria", methods=["GET", "POST"])
def auditoria():
    if "usuario" not in session or session["tipo"] != "admin":
        flash("🚫 Solo administradores pueden acceder a la auditoría.", "danger")
        return redirect("/login")

    db = get_db()
    unidad_id = request.args.get("unidad_id", "")
    usuario_id = request.args.get("usuario_id", "")
    mes = request.args.get("mes", "")
    año = request.args.get("año", "")

    unidades = db.execute("SELECT id, nombre FROM unidad WHERE activo=1").fetchall()
    usuarios = db.execute("SELECT id, nombre FROM usuarios WHERE activo=1").fetchall()

    query = """
    SELECT r.id, r.valor, r.mes, r.año, r.fecha_ingreso,
           p.texto AS pregunta, p.afecta_presupuesto,
           pr.nombre AS presupuesto, u.nombre AS unidad, us.nombre AS usuario
    FROM respuestas r
    JOIN preguntas p ON r.pregunta_id = p.id
    LEFT JOIN unidad u ON p.unidad_id = u.id
    LEFT JOIN usuarios us ON r.usuario_id = us.id
    LEFT JOIN presupuesto pr ON p.presupuesto_id = pr.id
    WHERE 1=1
    """
    params = []

    if unidad_id:
        query += " AND u.id = ?"
        params.append(unidad_id)
    if usuario_id:
        query += " AND us.id = ?"
        params.append(usuario_id)
    if mes:
        query += " AND r.mes = ?"
        params.append(mes)
    if año:
        query += " AND r.año = ?"
        params.append(año)

    query += " ORDER BY r.año DESC, r.mes DESC, us.nombre"
    respuestas = db.execute(query, params).fetchall()

    return render_template(
        "auditoria.html",
        respuestas=respuestas,
        unidades=unidades,
        usuarios=usuarios,
        filtros={"unidad_id": unidad_id, "usuario_id": usuario_id, "mes": mes, "año": año}
    )


# ======================================
# DESCARGAR PLANILLA DE EJEMPLO
# ======================================
@auditoria_bp.route("/auditoria/ejemplo")
def auditoria_ejemplo():
    df = pd.DataFrame({
        "pregunta_id": [1, 2],
        "valor": ["Texto o número", "Ejemplo de respuesta"],
        "mes": ["Noviembre", "Noviembre"],
        "año": [2025, 2025],
        "usuario_nombre": ["usuario1", "usuario1"],
        "afecta_presupuesto": ["Sí", "No"],
        "presupuesto_nombre": ["Presupuesto General", "No aplica"]
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Respuestas_Ejemplo")

    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Planilla_Respuestas_Ejemplo.xlsx")


# ======================================
# IMPORTAR RESPUESTAS MASIVAS DESDE EXCEL
# ======================================
@auditoria_bp.route("/auditoria/importar", methods=["POST"])
def auditoria_importar():
    if "usuario" not in session or session["tipo"] != "admin":
        flash("🚫 Solo administradores pueden importar respuestas.", "danger")
        return redirect("/login")

    archivo = request.files.get("archivo")
    if not archivo:
        flash("⚠️ No se seleccionó ningún archivo.", "warning")
        return redirect(url_for("auditoria.auditoria"))

    try:
        df = pd.read_excel(archivo)
    except Exception as e:
        flash(f"❌ Error al leer el archivo: {str(e)}", "danger")
        return redirect(url_for("auditoria.auditoria"))

    columnas_requeridas = {"pregunta_id", "valor", "mes", "año", "usuario_nombre"}
    if not columnas_requeridas.issubset(df.columns):
        flash("⚠️ El archivo debe contener al menos las columnas: pregunta_id, valor, mes, año, usuario_nombre", "warning")
        return redirect(url_for("auditoria.auditoria"))

    db = get_db()
    total_insertadas = 0
    total_omitidas = 0
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, fila in df.iterrows():
        usuario = db.execute("SELECT id FROM usuarios WHERE nombre=?", (fila["usuario_nombre"],)).fetchone()
        if not usuario:
            total_omitidas += 1
            continue

        existente = db.execute("""
            SELECT id FROM respuestas
            WHERE pregunta_id=? AND usuario_id=? AND mes=? AND año=?
        """, (fila["pregunta_id"], usuario["id"], fila["mes"], fila["año"])).fetchone()
        if existente:
            total_omitidas += 1
            continue

        # Nuevas columnas opcionales
        afecta_presupuesto = 0
        presupuesto_id = None

        if "afecta_presupuesto" in df.columns:
            afecta_presupuesto = 1 if str(fila["afecta_presupuesto"]).strip().lower() in ["sí", "si", "yes", "1"] else 0

        if "presupuesto_nombre" in df.columns and pd.notna(fila["presupuesto_nombre"]):
            presupuesto = db.execute("SELECT id FROM presupuesto WHERE nombre=?", (fila["presupuesto_nombre"],)).fetchone()
            if presupuesto:
                presupuesto_id = presupuesto["id"]

        # Insertar respuesta
        db.execute("""
            INSERT INTO respuestas (pregunta_id, usuario_id, valor, mes, año, fecha_ingreso)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fila["pregunta_id"], usuario["id"], str(fila["valor"]), fila["mes"], fila["año"], fecha))
        total_insertadas += 1

        # Si está afecto, actualiza la pregunta
        if presupuesto_id and afecta_presupuesto == 1:
            db.execute("""
                UPDATE preguntas
                SET afecta_presupuesto=?, presupuesto_id=?
                WHERE id=?
            """, (1, presupuesto_id, fila["pregunta_id"]))

    db.commit()
    flash(f"✅ {total_insertadas} respuestas cargadas correctamente. {total_omitidas} omitidas.", "success")
    return redirect(url_for("auditoria.auditoria"))


# ======================================
# EXPORTAR TODAS LAS RESPUESTAS FILTRADAS
# ======================================
@auditoria_bp.route("/auditoria/exportar")
def auditoria_exportar():
    db = get_db()
    data = db.execute("""
        SELECT r.id, p.texto AS pregunta, r.valor, r.mes, r.año,
               us.nombre AS usuario, un.nombre AS unidad, pr.nombre AS presupuesto
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id = p.id
        LEFT JOIN usuarios us ON r.usuario_id = us.id
        LEFT JOIN unidad un ON p.unidad_id = un.id
        LEFT JOIN presupuesto pr ON p.presupuesto_id = pr.id
        ORDER BY r.año DESC, r.mes DESC
    """).fetchall()

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Respuestas")

    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Respuestas_Auditoria.xlsx")


# ======================================
# EDITAR RESPUESTA
# ======================================
@auditoria_bp.route("/auditoria/editar/<int:id>", methods=["GET", "POST"])
def auditoria_editar(id):
    db = get_db()
    respuesta = db.execute("""
        SELECT r.*, p.texto AS pregunta, us.nombre AS usuario
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id = p.id
        LEFT JOIN usuarios us ON r.usuario_id = us.id
        WHERE r.id=?
    """, (id,)).fetchone()

    if not respuesta:
        flash("❌ Respuesta no encontrada.", "danger")
        return redirect(url_for("auditoria.auditoria"))

    if request.method == "POST":
        nuevo_valor = request.form["valor"]
        db.execute("UPDATE respuestas SET valor=? WHERE id=?", (nuevo_valor, id))
        db.commit()
        flash("✏️ Respuesta actualizada correctamente.", "success")
        return redirect(url_for("auditoria.auditoria"))

    return render_template("editar_respuesta.html", respuesta=respuesta)


# ======================================
# ELIMINAR RESPUESTA
# ======================================
@auditoria_bp.route("/auditoria/eliminar/<int:id>")
def auditoria_eliminar(id):
    db = get_db()
    existe = db.execute("SELECT id FROM respuestas WHERE id=?", (id,)).fetchone()
    if not existe:
        flash("⚠️ La respuesta no existe o ya fue eliminada.", "warning")
        return redirect(url_for("auditoria.auditoria"))

    db.execute("DELETE FROM respuestas WHERE id=?", (id,))
    db.commit()
    flash("🗑️ Respuesta eliminada correctamente.", "success")
    return redirect(url_for("auditoria.auditoria"))
