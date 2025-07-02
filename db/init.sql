CREATE DATABASE IF NOT EXISTS db01;
USE db01;

CREATE TABLE IF NOT EXISTS Usuarios (
    usuario_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    tipo ENUM('paciente', 'doctor', 'admin') NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultimo_login DATETIME,
    activo TINYINT(1) DEFAULT 1,
    INDEX idx_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Especialidades (
    especialidad_id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    INDEX idx_nombre (nombre)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Pacientes (
    paciente_id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero ENUM('Masculino', 'Femenino', 'Otro') NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(usuario_id) ON DELETE CASCADE,
    INDEX idx_nombre_apellido (nombre, apellido)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Doctores (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    especialidad_id INT NOT NULL,
    telefono VARCHAR(20),
    numero_licencia VARCHAR(50) UNIQUE NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (especialidad_id) REFERENCES Especialidades(especialidad_id) ON DELETE RESTRICT,
    INDEX idx_nombre_apellido (nombre, apellido),
    INDEX idx_especialidad (especialidad_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Administradores (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(usuario_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Horarios_Doctores (
    horario_id INT PRIMARY KEY AUTO_INCREMENT,
    doctor_id INT NOT NULL,
    dia_semana ENUM('Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    duracion_cita INT DEFAULT 30 COMMENT 'Duración en minutos',
    FOREIGN KEY (doctor_id) REFERENCES Doctores(doctor_id) ON DELETE CASCADE,
    INDEX idx_doctor_dia (doctor_id, dia_semana)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Citas (
    cita_id INT PRIMARY KEY AUTO_INCREMENT,
    paciente_id INT NOT NULL,
    doctor_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    estado ENUM('Programada', 'Confirmada', 'Completada', 'Cancelada', 'No asistió') DEFAULT 'Programada',
    motivo TEXT,
    notas TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES Pacientes(paciente_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctores(doctor_id) ON DELETE RESTRICT,
    INDEX idx_fecha_hora (fecha_hora),
    INDEX idx_paciente_estado (paciente_id, estado),
    INDEX idx_doctor_estado (doctor_id, estado)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Historial_Medico (
    historial_id INT PRIMARY KEY AUTO_INCREMENT,
    paciente_id INT NOT NULL,
    doctor_id INT NOT NULL,
    cita_id INT,
    fecha_consulta DATETIME NOT NULL,
    diagnostico TEXT,
    tratamiento TEXT,
    notas TEXT,
    FOREIGN KEY (paciente_id) REFERENCES Pacientes(paciente_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctores(doctor_id) ON DELETE RESTRICT,
    FOREIGN KEY (cita_id) REFERENCES Citas(cita_id) ON DELETE SET NULL,
    INDEX idx_paciente_fecha (paciente_id, fecha_consulta)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Recetas (
    receta_id INT PRIMARY KEY AUTO_INCREMENT,
    historial_id INT NOT NULL,
    medicamento VARCHAR(100) NOT NULL,
    dosis VARCHAR(100),
    frecuencia VARCHAR(100),
    duracion VARCHAR(100),
    instrucciones TEXT,
    fecha_emision DATE NOT NULL,
    FOREIGN KEY (historial_id) REFERENCES Historial_Medico(historial_id) ON DELETE CASCADE,
    INDEX idx_historial (historial_id),
    INDEX idx_fecha_emision (fecha_emision)
) ENGINE=InnoDB;