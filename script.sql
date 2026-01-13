CREATE DATABASE ControlAsistencia;
USE ControlAsistencia;

CREATE TABLE administradores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    rol VARCHAR(50) DEFAULT 'Admin',
    activo TINYINT DEFAULT 1 COMMENT '1=Activo, 0=Inactivo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    INDEX idx_usuario (usuario),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL UNIQUE,
    imagen_registro VARCHAR(255),
    fecha_registro DATETIME
);

CREATE TABLE asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    tipo TINYINT NOT NULL COMMENT '0=INDETERMINADO, 1=ENTRADA, 2=SALIDA',
    estado TINYINT NOT NULL COMMENT '0=INDETERMINADO, 1=NORMAL, 2=TARDANZA',
    minutos_extra INT DEFAULT 0,   -- Positivo = tiempo extra trabajado
    observacion VARCHAR(255),    -- Descripción/justificación
    similitud DECIMAL(5,4),
    imagen_asistencia VARCHAR(255) NOT NULL,

    FOREIGN KEY (nombre_usuario) REFERENCES usuarios(nombre_usuario) 
    ON DELETE CASCADE 
    ON UPDATE CASCADE
);
/*
tipo:
--1 = ENTRADA
--0 = SALIDA
--estado:
--1 = PUNTUAL
--0 = TARDE
*/
select*from asistencias;
DELETE FROM usuarios
WHERE id > 0;