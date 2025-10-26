import os
import sqlalchemy
from flask import Flask, jsonify, request
from google.cloud.sql.connector import Connector, IPTypes

# =================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS (NO TOCAR)
# =================================================================

# Lee las variables de entorno que configuraremos en Cloud Run
db_user = os.environ.get("DB_USER")          # ej: postgres
db_pass = os.environ.get("DB_PASS")          # Tomado de Secret Manager
db_name = os.environ.get("DB_NAME")          # ej: agrovida
instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME") # ej: proyecto:region:instancia

# Inicializa el conector de Cloud SQL
connector = Connector()

# Función para obtener una conexión a la base de datos
def getconn():
    conn = connector.connect(
        instance_connection_name,
        "pg8000",  # Driver para PostgreSQL (si usas MySQL, cambia a "mysql+pymysql")
        user=db_user,
        password=db_pass,
        db=db_name,
        ip_type=IPTypes.PRIVATE  # Usa IP privada para mejor seguridad
    )
    return conn

# Inicializa el "pool" de conexiones con SQLAlchemy
pool = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
)

# =================================================================
# INICIO DE LA API (FLASK)
# =================================================================
app = Flask(__name__)

# Endpoint para OBTENER comentarios de un terreno
@app.route("/comentarios/<int:terreno_id>", methods=["GET"])
def get_comentarios(terreno_id):
    try:
        with pool.connect() as db_conn:
            # Ejecuta la consulta SQL
            result = db_conn.execute(
                sqlalchemy.text("SELECT texto, fecha FROM comentarios WHERE terreno_id = :id ORDER BY fecha DESC"),
                {"id": terreno_id}
            ).fetchall()
            
            # Formatea la respuesta como JSON
            comentarios = [{"texto": row[0], "fecha": row[1].isoformat()} for row in result]
            return jsonify(comentarios), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para AÑADIR un nuevo comentario
@app.route("/comentarios", methods=["POST"])
def add_comentario():
    try:
        # Obtiene los datos JSON que envía la app de Android
        data = request.get_json()
        
        if not data or "terreno_id" not in data or "texto" not in data:
            return jsonify({"error": "Faltan datos 'terreno_id' o 'texto'"}), 400

        terreno_id = data["terreno_id"]
        texto = data["texto"]

        with pool.connect() as db_conn:
            # Prepara la sentencia SQL para insertar
            stmt = sqlalchemy.text(
                "INSERT INTO comentarios (terreno_id, texto) VALUES (:terreno_id, :texto)"
            )
            # Ejecuta la inserción
            db_conn.execute(stmt, {"terreno_id": terreno_id, "texto": texto})
            db_conn.commit() # Confirma la transacción
            
            return jsonify({"mensaje": "Comentario guardado"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =================================================================
# EJECUCIÓN DEL SERVIDOR
# =================================================================
if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )