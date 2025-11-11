import sqlite3
from flask import Blueprint, render_template, request

auditoria_bp = Blueprint('auditoria', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------
# PANEL DE AUDITORÍA ADMIN
# -------------------------------
@auditoria_bp.route("/auditoria", methods=["GET", "POST"])
def auditoria():
    db = get_db()

    # Filtros desde el formulario
    unidad_id = request.args.get("unidad_id", "")
    usuario_id = request.args.get("usuario_id", "")
    mes = request.args.get("mes", "")
    año = request.args.get("año", "")

    # Obtener listas de opciones
    unidades = db.execute("SELECT id, nombre FROM unidad WHERE activo=1").fetchall()
    usuarios = db.execute("SELECT id, nombre FROM usuarios WHERE activo=1").fetchall()

    # Construcción dinámica de la consulta SQL
    query = """
    SELECT r.id, r.valor, r.mes, r.año, r.fecha_ingreso,
           p.texto AS pregunta, u.nombre AS unidad, us.nombre AS usuario, pr.nombre AS presupuesto
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
