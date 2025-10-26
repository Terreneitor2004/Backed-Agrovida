from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras # Importante para mejores diccionarios
import os

app = Flask(__name__)

# -------------------------------------------------------
# 🔹 CONFIGURACIÓN DE CONEXIÓN A CLOUD SQL
# -------------------------------------------------------
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")
DB_HOST = os.environ.get("DB_HOST")

def get_connection():
    # psycopg2.connect puede lanzar una excepción si las credenciales
    # o el host son incorrectos, por eso debe estar en un try/except.
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
    conn = None # Inicializamos la conexión como None
    try:
        conn = get_connection()
        # Usamos un cursor que devuelve diccionarios para el GET
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
            nuevo_id = cur.fetchone()["id"] # Obtenemos el ID del terreno insertado
            conn.commit()
            
            return jsonify({
                "status": "ok", 
                "message": "Terreno guardado correctamente",
                "id": nuevo_id
            }), 201 # 201 Created es mejor para un POST exitoso

        # --- Método GET ---
        cur.execute("SELECT id, nombre, latitud, longitud FROM terrenos ORDER BY id DESC")
        # Al usar DictCursor, 'rows' será una lista de diccionarios
        rows = cur.fetchall() 
        
        # Convertimos las filas (que son DictRow) a diccionarios estándar
        return jsonify([dict(row) for row in rows])

    except (Exception, psycopg2.DatabaseError) as e:
        # ¡ESTO ES CLAVE! Captura cualquier error de BD
        # Si hubo un error en la transacción, hacemos rollback
        if conn:
            conn.rollback() 
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        # ¡ESTO TAMBIÉN ES CLAVE! Asegura que la conexión SIEMPRE se cierre
        if cur:
            cur.close()
        if conn:
            conn.close()

# -------------------------------------------------------
# 🔹 TEST DE CONEXIÓN A LA BD
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
        # Devuelve el error específico de conexión
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