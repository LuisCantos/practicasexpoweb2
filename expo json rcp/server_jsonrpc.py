# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Configuracion de la base de datos
DB_CONFIG = {
    "dbname": "jsonrpc",
    "user": "luis",          # <-- tu usuario de PostgreSQL
    "password": "123456", # <-- pon tu contraseña real
    "host": "localhost",
    "port": "5432"
}

# Funcion para conectar a la base de datos
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route("/jsonrpc", methods=["POST"])
def jsonrpc():
    data = request.get_json()
    metodo = data.get("method")
    params = data.get("params", [])
    id_rpc = data.get("id", None)

    try:
        if metodo == "sumar":
            resultado = sum(params)
            return jsonify({"jsonrpc": "2.0", "result": resultado, "id": id_rpc})

        elif metodo == "insertar_usuario":
            nombre, edad = params
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO usuarios (nombre, edad) VALUES (%s, %s)", (nombre, edad))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"jsonrpc": "2.0", "result": "Usuario insertado correctamente", "id": id_rpc})

        elif metodo == "listar_usuarios":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM usuarios")
            filas = cur.fetchall()
            cur.close()
            conn.close()
            usuarios = [{"id": f[0], "nombre": f[1], "edad": f[2]} for f in filas]
            return jsonify({"jsonrpc": "2.0", "result": usuarios, "id": id_rpc})

        elif metodo == "eliminar_usuario":
            user_id = params[0]
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"jsonrpc": "2.0", "result": f"Usuario {user_id} eliminado", "id": id_rpc})

        else:
            return jsonify({"jsonrpc": "2.0", "error": f"Metodo '{metodo}' no encontrado", "id": id_rpc})

    except Exception as e:
        return jsonify({"jsonrpc": "2.0", "error": str(e), "id": id_rpc})

if __name__ == "__main__":
    app.config["JSON_AS_ASCII"] = False  # evita errores de UTF-8
    app.run(port=5000, debug=True)


