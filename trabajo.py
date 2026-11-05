from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from google import genai

app = Flask(__name__)
CORS(app) 

# Usamos /tmp para que Render nos deje escribir
DB_FILE = "/tmp/sistema_registro.db"

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    cliente_ia = genai.Client(api_key=API_KEY)
else:
    cliente_ia = None

def inicializar_base_datos():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    
    # IMPORTANTE: Aquí se crea la columna fecha_registro
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            cedula TEXT PRIMARY KEY, 
            nombre1 TEXT NOT NULL, 
            nombre2 TEXT,
            apellido1 TEXT NOT NULL, 
            apellido2 TEXT, 
            telefono TEXT, 
            direccion TEXT,
            fecha_registro TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            usuario TEXT PRIMARY KEY, 
            password TEXT NOT NULL
        )
    """)
    
    try:
        cursor.execute("INSERT INTO admin (usuario, password) VALUES ('admin', '1234')")
    except sqlite3.IntegrityError:
        pass 
        
    conexion.commit()
    conexion.close()

def obtener_conexion():
    conexion = sqlite3.connect(DB_FILE)
    conexion.row_factory = sqlite3.Row 
    return conexion

@app.route('/login', methods=['POST'])
def login():
    datos = request.json
    usuario = datos.get('usuario')
    password = datos.get('password')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM admin WHERE usuario = ? AND password = ?", (usuario, password))
    resultado = cursor.fetchone()
    conexion.close()
    
    if resultado:
        return jsonify({"exito": True, "mensaje": "Bienvenido"})
    else:
        return jsonify({"exito": False, "mensaje": "Usuario o contraseña incorrectos"})

@app.route('/procesar', methods=['POST'])
def procesar():
    datos = request.json
    accion = datos.get('accion')
    cedula = datos.get('cedula')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    respuesta = {"mensaje": "Acción no reconocida", "datos": None}
    
    try:
        if accion == 'guardar':
            sql = """INSERT INTO usuarios (cedula, nombre1, nombre2, apellido1, apellido2, telefono, direccion, fecha_registro) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))"""
            valores = (cedula, datos['nombre1'], datos['nombre2'], datos['apellido1'], datos['apellido2'], datos['telefono'], datos['direccion'])
            cursor.execute(sql, valores)
            conexion.commit()
            respuesta["mensaje"] = "Registro guardado exitosamente."
            
        elif accion == 'consultar':
            sql = "SELECT * FROM usuarios WHERE cedula = ?"
            cursor.execute(sql, (cedula,))
            resultado = cursor.fetchone()
            if resultado:
                respuesta["mensaje"] = "Usuario encontrado."
                respuesta["datos"] = dict(resultado) 
            else:
                respuesta["mensaje"] = "Usuario no registrado."
                
        elif accion == 'editar':
            sql = """UPDATE usuarios SET nombre1=?, nombre2=?, apellido1=?, apellido2=?, telefono=?, direccion=? 
                     WHERE cedula=?"""
            valores = (datos['nombre1'], datos['nombre2'], datos['apellido1'], datos['apellido2'], datos['telefono'], datos['direccion'], cedula)
            cursor.execute(sql, valores)
            conexion.commit()
            respuesta["mensaje"] = "Registro actualizado exitosamente."
            
        elif accion == 'eliminar':
            sql = "DELETE FROM usuarios WHERE cedula = ?"
            cursor.execute(sql, (cedula,))
            conexion.commit()
            respuesta["mensaje"] = "Registro eliminado exitosamente."
            
    except sqlite3.IntegrityError:
        respuesta["mensaje"] = "Aviso: Esta cédula ya está registrada en el sistema."
    except sqlite3.Error as err:
        respuesta["mensaje"] = f"Error en la base de datos: {err}"
    except KeyError as err:
        respuesta["mensaje"] = f"Falta un campo en los datos enviados: {err}"
    finally:
        cursor.close()
        conexion.close()
        
    return jsonify(respuesta)

@app.route('/exportar', methods=['GET'])
def exportar():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios")
    resultados = cursor.fetchall()
    conexion.close()
    
    lista_usuarios = [dict(fila) for fila in resultados]
    return jsonify({"exito": True, "datos": lista_usuarios})

@app.route('/lista_usuarios', methods=['GET'])
def lista_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY apellido1 ASC")
    resultados = cursor.fetchall()
    conexion.close()
    
    lista_usuarios = [dict(fila) for fila in resultados]
    return jsonify({"exito": True, "datos": lista_usuarios})

@app.route('/agente_ia', methods=['POST'])
def agente_ia():
    if not cliente_ia:
         return jsonify({"respuesta": "Error: El agente de IA no está configurado."})
         
    datos = request.json
    pregunta = datos.get('pregunta')
    if not pregunta:
        return jsonify({"respuesta": "Por favor, haz una pregunta."})
        
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT cedula, nombre1, apellido1, telefono FROM usuarios")
    resultados = cursor.fetchall()
    conexion.close()
    
    lista_usuarios = [dict(fila) for fila in resultados]
    contexto_datos = f"Usuarios registrados: {lista_usuarios}" if lista_usuarios else "La base de datos está vacía."
    
    prompt = f"""
    Eres un asistente virtual para un sistema de registro.
    Datos de la base de datos: {contexto_datos}
    Instrucciones: Responde de forma clara y concisa. Si no está en la lista, di que no existe.
    Pregunta: {pregunta}
    """
    
    try:
        respuesta_ia = cliente_ia.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return jsonify({"respuesta": respuesta_ia.text})
    except Exception as e:
        return jsonify({"respuesta": f"Error en la IA: {str(e)}"})

# 🔥 ESTO ES CLAVE: Crear tablas al arrancar para que Gunicorn las detecte
inicializar_base_datos()

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto)

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto)
