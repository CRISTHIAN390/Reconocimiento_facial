CREATE DATABASE ControlAsistencia;
USE ControlAsistencia;
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL UNIQUE,
    imagen_registro VARCHAR(255),
    fecha_registro DATETIME
);

CREATE TABLE asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    similitud DECIMAL(5,4),
    imagen_asistencia VARCHAR(255)
);
select*from asistencias;
DELETE FROM asistencias
WHERE id > 0;