from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras 
import os

app = Flask(__name__)

# -------------------------------------------------------
# 🔹 CONFIGURACIÓN DE CONEXIÓN A CLOUD SQL
# -------------------------------------------------------
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")
# Usamos la IP pública, tal como se corrigió
DB_HOST = os.environ.get("DB_HOST") 

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
    return "🚜 Servicio AgroVida activo - módulos terrenos y comentarios"

# -------------------------------------------------------
# 🔹 RUTA DE TERRENOS (GET / POST)
# -------------------------------------------------------
@app.route("/terrenos", methods=["GET", "POST"])
def terrenos():
    conn = None 
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "POST":
            data = request.get_json()
            nombre = data.get("nombre")
            latitud = data.get("latitud")
            longitud = data.get("longitud")

            if not nombre or latitud is None or longitud is None:
                return jsonify({"error": "Faltan datos obligatorios (nombre, latitud, longitud)"}), 400

            cur.execute(
                "INSERT INTO terrenos (nombre, latitud, longitud) VALUES (%s, %s, %s) RETURNING id",
                (nombre, latitud, longitud)
            )
            nuevo_id = cur.fetchone()["id"]
            conn.commit()
            
            return jsonify({
                "status": "ok", 
                "message": "Terreno guardado correctamente",
                "id": nuevo_id
            }), 201

        # --- Método GET ---
        cur.execute("SELECT id, nombre, latitud, longitud FROM terrenos ORDER BY id DESC")
        rows = cur.fetchall() 
        
        return jsonify([dict(row) for row in rows])

    except (Exception, psycopg2.DatabaseError) as e:
        if conn:
            conn.rollback() 
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------------------------------------------
# 🔹 RUTA DE COMENTARIOS (GET / POST)
# -------------------------------------------------------
@app.route("/comentarios", methods=["POST"])
def post_comentario():
    conn = None 
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        data = request.get_json()
        terreno_id = data.get("terreno_id")
        texto = data.get("texto")

        # Validación
        if not terreno_id or not texto:
            return jsonify({"error": "Faltan datos obligatorios (terreno_id, texto)"}), 400
        
        # Validar que terreno_id sea un número entero
        try:
            terreno_id = int(terreno_id)
        except ValueError:
            return jsonify({"error": "terreno_id debe ser un número entero"}), 400

        # Inserción
        cur.execute(
            "INSERT INTO comentarios (terreno_id, texto) VALUES (%s, %s) RETURNING id, fecha",
            (terreno_id, texto)
        )
        result = cur.fetchone()
        conn.commit()
        
        return jsonify({
            "status": "ok", 
            "message": "Comentario guardado",
            "id": result["id"],
            "fecha": str(result["fecha"])
        }), 201

    except (Exception, psycopg2.DatabaseError) as e:
        if conn:
            conn.rollback() 
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------------------------------------------
# 🔹 RUTA PARA OBTENER COMENTARIOS POR TERRENO
# -------------------------------------------------------
@app.route("/comentarios/<int:terreno_id>", methods=["GET"])
def get_comentarios(terreno_id):
    conn = None 
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute(
            "SELECT id, texto, fecha FROM comentarios WHERE terreno_id = %s ORDER BY fecha DESC",
            (terreno_id,)
        )
        rows = cur.fetchall()
        
        # Convertimos las filas a diccionarios y formateamos la fecha
        comentarios_list = []
        for row in rows:
            comentarios_list.append({
                "id": row["id"], 
                "texto": row["texto"], 
                "fecha": str(row["fecha"]) # Convertir el timestamp a string
            })
            
        return jsonify(comentarios_list)

    except (Exception, psycopg2.DatabaseError) as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------------------------------------------
# 🔹 TEST DE CONEXIÓN A LA BD (mantenido por si acaso)
# -------------------------------------------------------
@app.route("/test-db")
def test_db():
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW()")
        result = cur.fetchone()
        return jsonify({"status": "ok", "db_time": str(result[0])})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------------------------------------------
# 🔹 EJECUCIÓN PRINCIPAL
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)