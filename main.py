from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# -------------------------------------------------------
# 🔹 CONFIGURACIÓN DE CONEXIÓN A CLOUD SQL
# -------------------------------------------------------
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")
DB_HOST = os.environ.get("DB_HOST")  # IP pública o socket unix

def get_connection():
    return psycopg2.connect(
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=DB_HOST
    )

# -------------------------------------------------------
# 🔹 RUTA PRINCIPAL
# -------------------------------------------------------
@app.route("/")
def home():
    return "🚜 Servicio AgroVida activo - módulo terrenos"

# -------------------------------------------------------
# 🔹 RUTA DE TERRENOS (GET / POST)
# -------------------------------------------------------
@app.route("/terrenos", methods=["GET", "POST"])
def terrenos():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.get_json()
        nombre = data.get("nombre")
        latitud = data.get("latitud")
        longitud = data.get("longitud")

        if not nombre or latitud is None or longitud is None:
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        cur.execute(
            "INSERT INTO terrenos (nombre, latitud, longitud) VALUES (%s, %s, %s)",
            (nombre, latitud, longitud)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Terreno guardado correctamente"})

    cur.execute("SELECT id, nombre, latitud, longitud FROM terrenos ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "nombre": r[1], "latitud": r[2], "longitud": r[3]}
        for r in rows
    ])

# -------------------------------------------------------
# 🔹 TEST DE CONEXIÓN A LA BD (opcional)
# -------------------------------------------------------
@app.route("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW()")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "db_time": str(result[0])})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# -------------------------------------------------------
# 🔹 EJECUCIÓN PRINCIPAL
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
