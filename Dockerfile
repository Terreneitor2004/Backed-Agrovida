import os
import sqlalchemy
from flask import Flask, jsonify, request
from google.cloud.sql.connector import Connector, IPTypes
from datetime import datetime # Importado para manejar fechas

# =================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS (NO TOCAR)
# =================================================================

db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")
instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")

connector = Connector()

def getconn():
    conn = connector.connect(
        instance_connection_name,
        "pg8000", # Driver para PostgreSQL
        user=db_user,
        password=db_pass,
        db=db_name,
        ip_type=IPTypes.PRIVATE
    )
    return conn

pool = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
)

# =================================================================
# INICIO DE LA API (FLASK)
# =================================================================
app = Flask(__name__)

# --- ENDPOINTS DE TERRENOS ---

# [NUEVO] Endpoint para OBTENER todos los terrenos
@app.route("/terrenos", methods=["GET"])
def get_terrenos():
    try:
        with pool.connect() as db_conn:
            result = db_conn.execute(
                sqlalchemy.text("SELECT id, nombre, latitud, longitud FROM terrenos")
            ).fetchall()
            
            terrenos = [
                {"id": row[0], "nombre": row[1], "latitud": row[2], "longitud": row[3]}
                for row in result
            ]
            return jsonify(terrenos), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ENDPOINTS DE COMENTARIOS ---

# [CORREGIDO] Endpoint para OBTENER comentarios de un terreno
@app.route("/comentarios/<int:terreno_id>", methods=["GET"])
def get_comentarios(terreno_id):
    try:
        with pool.connect() as db_conn:
            # CORREGIDO: Ahora seleccionamos el 'id' y 'terreno_id'
            result = db_conn.execute(
                sqlalchemy.text(
                    "SELECT id, terreno_id, texto, fecha FROM comentarios "
                    "WHERE terreno_id = :id ORDER BY fecha DESC"
                ),
                {"id": terreno_id}
            ).fetchall()
            
            # CORREGIDO: El JSON ahora incluye todos los campos
            comentarios = [
                {
                    "id": row[0], 
                    "terreno_id": row[1], 
                    "texto": row[2], 
                    "fecha": row[3].isoformat() # Convertimos fecha a string ISO
                } 
                for row in result
            ]
            return jsonify(comentarios), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# [EXISTENTE] Endpoint para AÑADIR un nuevo comentario
@app.route("/comentarios", methods=["POST"])
def add_comentario():
    try:
        data = request.get_json()
        
        if not data or "terreno_id" not in data or "texto" not in data:
            return jsonify({"error": "Faltan datos 'terreno_id' o 'texto'"}), 400

        with pool.connect() as db_conn:
            stmt = sqlalchemy.text(
                "INSERT INTO comentarios (terreno_id, texto, fecha) "
                "VALUES (:terreno_id, :texto, :fecha)"
            )
            # Añadimos fecha actual
            db_conn.execute(
                stmt, 
                {
                    "terreno_id": data["terreno_id"], 
                    "texto": data["texto"],
                    "fecha": datetime.utcnow() # Usar fecha del servidor
                }
            )
            db_conn.commit()
            
            return jsonify({"mensaje": "Comentario guardado"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# [NUEVO] Endpoint para EDITAR un comentario existente
@app.route("/comentarios/<int:comentario_id>", methods=["PUT"])
def update_comentario(comentario_id):
    try:
        data = request.get_json()
        if not data or "texto" not in data:
            return jsonify({"error": "Falta el campo 'texto'"}), 400

        with pool.connect() as db_conn:
            stmt = sqlalchemy.text(
                "UPDATE comentarios SET texto = :texto WHERE id = :id"
            )
            result = db_conn.execute(stmt, {"texto": data["texto"], "id": comentario_id})
            db_conn.commit()
            
            # rowcount nos dice cuántas filas fueron afectadas. Si es 0, no se encontró el ID.
            if result.rowcount == 0:
                 return jsonify({"error": "Comentario no encontrado"}), 404
                 
            return jsonify({"mensaje": "Comentario actualizado"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# [NUEVO] Endpoint para ELIMINAR un comentario
@app.route("/comentarios/<int:comentario_id>", methods=["DELETE"])
def delete_comentario(comentario_id):
    try:
        with pool.connect() as db_conn:
            stmt = sqlalchemy.text("DELETE FROM comentarios WHERE id = :id")
            result = db_conn.execute(stmt, {"id": comentario_id})
            db_conn.commit()

            if result.rowcount == 0:
                 return jsonify({"error": "Comentario no encontrado"}), 404

            return jsonify({"mensaje": "Comentario eliminado"}), 200

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