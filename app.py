from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
from dotenv import load_dotenv
import bcrypt
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mys3cr3tk3y'

load_dotenv()

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'user')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'password')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'db01')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_CONNECT_TIMEOUT'] = 30

mysql = MySQL(app)

def init_db_connection():
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            print(f"Intento {attempt + 1} de {max_retries}: Error conectando a MySQL - {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    return False

def initialize_database():
    """Función para crear datos iniciales necesarios"""
    try:
        cursor = mysql.connection.cursor()
        
        # 1. Crear especialidades si no existen
        cursor.execute("SELECT COUNT(*) FROM Especialidades")
        if cursor.fetchone()['COUNT(*)'] == 0:
            especialidades = [
                ('Cardiología', 'Especialidad del corazón'),
                ('Pediatría', 'Especialidad para niños'),
                ('Dermatología', 'Especialidad de la piel')
            ]
            cursor.executemany(
                "INSERT INTO Especialidades (nombre, descripcion) VALUES (%s, %s)",
                especialidades
            )
            mysql.connection.commit()
        
        # 2. Crear usuario doctor si no existe
        cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE email = 'doctor@clinica.com'")
        if cursor.fetchone()['COUNT(*)'] == 0:
            hashed_pw = bcrypt.hashpw('doctor123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO Usuarios (email, contrasena_hash, tipo) VALUES (%s, %s, %s)",
                ('doctor@clinica.com', hashed_pw, 'doctor')
            )
            mysql.connection.commit()
            usuario_id = cursor.lastrowid
            
            # Obtener ID de Cardiología
            cursor.execute("SELECT especialidad_id FROM Especialidades WHERE nombre = 'Cardiología'")
            especialidad_id = cursor.fetchone()['especialidad_id']
            
            # 3. Crear doctor
            cursor.execute(
                """INSERT INTO Doctores 
                (usuario_id, nombre, apellido, especialidad_id, telefono, numero_licencia) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (usuario_id, 'Carlos', 'Mendoza', especialidad_id, '999888777', 'LIC-12345')
            )
            mysql.connection.commit()
            doctor_id = cursor.lastrowid
            
            # 4. Crear horarios
            horarios = [
                (doctor_id, 'Lunes', '09:00:00', '17:00:00'),
                (doctor_id, 'Miercoles', '09:00:00', '17:00:00'),
                (doctor_id, 'Viernes', '09:00:00', '13:00:00')
            ]
            cursor.executemany(
                """INSERT INTO Horarios_Doctores 
                (doctor_id, dia_semana, hora_inicio, hora_fin) 
                VALUES (%s, %s, %s, %s)""",
                horarios
            )
            mysql.connection.commit()
            
        # 5. Crear paciente de prueba
        cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE email = 'test@gmail.com'")
        if cursor.fetchone()['COUNT(*)'] == 0:
            hashed_pw = bcrypt.hashpw('test'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO Usuarios (email, contrasena_hash, tipo) VALUES (%s, %s, %s)",
                ('test@gmail.com', hashed_pw, 'paciente')
            )
            mysql.connection.commit()
            usuario_id = cursor.lastrowid
            
            cursor.execute(
                """INSERT INTO Pacientes 
                (usuario_id, nombre, apellido, fecha_nacimiento, genero) 
                VALUES (%s, %s, %s, %s, %s)""",
                (usuario_id, 'Paciente', 'Prueba', '1990-01-01', 'Masculino')
            )
            mysql.connection.commit()
            
        cursor.close()
        print("✓ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"! Error inicializando datos: {e}")
        mysql.connection.rollback()

with app.app_context():
    if init_db_connection():
        initialize_database()
    else:
        print("✗ No se pudo conectar a la base de datos después de varios intentos")

@app.before_request
def before_request():
    try:
        mysql.connection.ping(reconnect=True)
    except Exception as e:
        print(f"Error verificando conexión: {e}")

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM Usuarios WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and bcrypt.checkpw(password, user['contrasena_hash'].encode('utf-8')):
            session['user_id'] = user['usuario_id']
            session['user_type'] = user['tipo']
            flash('Inicio de sesión exitoso!', 'success')
            return redirect(url_for('menu'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html', user_type=session['user_type'])

@app.route('/get_doctores')
def get_doctores():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT d.doctor_id, d.nombre, d.apellido, e.nombre as especialidad 
        FROM Doctores d
        JOIN Especialidades e ON d.especialidad_id = e.especialidad_id
    """)
    doctores = cursor.fetchall()
    cursor.close()
    return jsonify(doctores)

@app.route('/get_horarios/<int:doctor_id>', methods=['GET'])
def get_horarios(doctor_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT dia_semana, hora_inicio, hora_fin FROM Horarios_Doctores WHERE doctor_id = %s", (doctor_id,))
        horarios = cursor.fetchall()

        for horario in horarios:
            horario['hora_inicio'] = str(horario['hora_inicio']) 
            horario['hora_fin'] = str(horario['hora_fin'])       

        return jsonify(horarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crear_cita', methods=['POST'])
def crear_cita():
    if 'user_id' not in session or session['user_type'] != 'paciente':
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT paciente_id FROM Pacientes WHERE usuario_id = %s", (session['user_id'],))
        paciente = cursor.fetchone()
        
        if not paciente:
            return jsonify({'error': 'Paciente no encontrado'}), 400
            
        cursor.execute("""
            INSERT INTO Citas 
            (paciente_id, doctor_id, fecha_hora, estado, motivo) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            paciente['paciente_id'],
            data['doctor_id'],
            data['fecha_hora'],
            'Programada',
            data['motivo']
        ))
        
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mis_citas')
def mis_citas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    
    if session['user_type'] == 'paciente':
        cursor.execute("""
            SELECT c.cita_id, d.nombre as doctor_nombre, d.apellido as doctor_apellido,
                   e.nombre as especialidad, c.fecha_hora, c.estado, c.motivo
            FROM Citas c
            JOIN Doctores d ON c.doctor_id = d.doctor_id
            JOIN Especialidades e ON d.especialidad_id = e.especialidad_id
            JOIN Pacientes p ON c.paciente_id = p.paciente_id
            WHERE p.usuario_id = %s
            ORDER BY c.fecha_hora DESC
        """, (session['user_id'],))
    else:
        cursor.execute("""
            SELECT c.cita_id, p.nombre as paciente_nombre, p.apellido as paciente_apellido,
                   c.fecha_hora, c.estado, c.motivo
            FROM Citas c
            JOIN Pacientes p ON c.paciente_id = p.paciente_id
            JOIN Doctores d ON c.doctor_id = d.doctor_id
            WHERE d.usuario_id = %s
            ORDER BY c.fecha_hora DESC
        """, (session['user_id'],))
    
    citas = cursor.fetchall()
    cursor.close()
    
    for cita in citas:
        if isinstance(cita['fecha_hora'], str):
            cita['fecha_hora'] = datetime.strptime(cita['fecha_hora'], '%Y-%m-%d %H:%M:%S')
    
    return render_template('mis_citas.html', citas=citas, user_type=session['user_type'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)