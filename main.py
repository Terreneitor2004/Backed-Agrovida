from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# -------------------------------------------------------
# 🔹 CONFIGURACIÓN DE CONEXIÓN A CLOUD SQL
# -------------------------------------------------------
# Si estás probando localmente, puedes reemplazar estas líneas
# por tus datos reales, por ejemplo:
# DB_USER = "postgres"
# DB_PASS = "tu_contraseña"
# DB_NAME = "agrovida"
# DB_HOST = "34.xxx.xxx.xxx"

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
    return "🚜 Servicio AgroVida activo"

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
        ubicacion = data.get("ubicacion")
        tamano = data.get("tamano")
        cultivo = data.get("cultivo")

        if not nombre or not ubicacion:
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        cur.execute(
            """
            INSERT INTO terrenos (nombre, ubicacion, tamano, cultivo)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, ubicacion, tamano, cultivo)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Terreno registrado correctamente"})

    # Si es GET: devolver todos los terrenos
    cur.execute("SELECT id, nombre, ubicacion, tamano, cultivo FROM terrenos ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "nombre": r[1], "ubicacion": r[2], "tamano": r[3], "cultivo": r[4]}
        for r in rows
    ])

# -------------------------------------------------------
# 🔹 RUTA DE COMENTARIOS (GET / POST)
# -------------------------------------------------------
@app.route("/comentarios", methods=["GET", "POST"])
def comentarios():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.get_json()
        terreno_id = data.get("terreno_id")
        texto = data.get("texto")

        if not terreno_id or not texto:
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        cur.execute(
            "INSERT INTO comentarios (terreno_id, texto) VALUES (%s, %s)",
            (terreno_id, texto)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Comentario guardado correctamente"})

    cur.execute("SELECT id, terreno_id, texto, fecha FROM comentarios ORDER BY fecha DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {"id": r[0], "terreno_id": r[1], "texto": r[2], "fecha": str(r[3])}
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
