from flask import Flask, jsonify, request, Response
from functools import wraps
import mysql.connector

app = Flask(__name__)

# Configuración de la conexión a la base de datos MySQL
db_config = {
    "host": "localhost",
    "user": "root",  # Cambia esto si usas otro usuario
    "password": "123456",  # Cambia esto con la contraseña de tu MySQL
    "database": "gestion_usuarios"
}

# Función para conectar a la base de datos
def obtener_conexion():
    return mysql.connector.connect(**db_config)

# Función para verificar la autenticación básica (se aplica a rutas protegidas)
def verificar_autenticacion(func):
    @wraps(func)
    def decorador(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != 'admin' or auth.password != 'secreto123':
            return Response('Acceso no autorizado', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return func(*args, **kwargs)
    return decorador

# Ruta para obtener todos los usuarios (protegida por autenticación básica)
@app.route('/usuarios', methods=['GET'])
@verificar_autenticacion
def obtener_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(usuarios)

# Ruta para obtener un usuario por id (protegida por autenticación básica)
@app.route('/usuarios/<int:id>', methods=['GET'])
@verificar_autenticacion
def obtener_usuario(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()
    if usuario:
        return jsonify(usuario)
    return jsonify({"error": "Usuario no encontrado"}), 404

# Ruta para agregar un usuario (sin autenticación)
@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    nombre = request.form.get('nombre')

    # Validar que el nombre se haya proporcionado
    if not nombre:
        return jsonify({"error": "Nombre no proporcionado"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nombre) VALUES (%s)", (nombre,))
        conexion.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        conexion.close()
        return jsonify({"id": nuevo_id, "nombre": nombre}), 201
    except mysql.connector.Error as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        if e.errno == 1062:  # Código de error para clave duplicada
            return jsonify({"error": "Nombre de usuario ya existe"}), 409
        return jsonify({"error": "Error al agregar el usuario"}), 500

# Ruta para eliminar un usuario por id (protegida por autenticación básica)
@app.route('/usuarios/<int:id>', methods=['DELETE'])
@verificar_autenticacion
def eliminar_usuario(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    filas_afectadas = cursor.rowcount
    conexion.commit()
    cursor.close()
    conexion.close()
    if filas_afectadas > 0:
        return jsonify({"mensaje": f"Usuario con ID {id} eliminado correctamente"}), 200
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)

