from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Configuración de conexión a Cloud SQL
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

@app.route("/")
def home():
    return "Servicio AgroVida activo 🚜"

@app.route("/comentarios", methods=["GET", "POST"])
def comentarios():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.get_json()
        terreno_id = data.get("terreno_id")
        texto = data.get("texto")

        cur.execute(
            "INSERT INTO comentarios (terreno_id, texto) VALUES (%s, %s)",
            (terreno_id, texto)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "message": "Comentario guardado"})

    # Si es GET: devolver todos los comentarios
    cur.execute("SELECT id, terreno_id, texto, fecha FROM comentarios ORDER BY fecha DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {"id": r[0], "terreno_id": r[1], "texto": r[2], "fecha": str(r[3])}
        for r in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
