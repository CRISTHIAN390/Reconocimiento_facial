# 👤 Sistema de Reconocimiento Facial – Control de Asistencia

Sistema de **reconocimiento facial** desarrollado en **Python** que permite el **registro de usuarios** y la **toma de asistencia** mediante comparación facial, utilizando una base de datos **MySQL** para el almacenamiento de la información.

El sistema funciona de manera **local**, haciendo uso de la cámara del equipo y técnicas de visión por computadora.

En caso se quiera hacer de forma remota solo se tiene que cambiar las conexiones de la base de datos y el guardado de imagenes
---

## 🚀 Características

- 📸 Registro facial de usuarios
- 🧠 Comparación facial para validación de identidad
- 🕒 Registro automático de asistencia
- 🗄️ Almacenamiento de datos en MySQL
- 🔐 Uso de variables de entorno (`.env`) para credenciales
- 📊 Precisión basada en embeddings faciales
- 💻 Sistema local (no requiere conexión a internet)

---

## 🛠️ Tecnologías Utilizadas

- **Python 3.10**
- **OpenCV**
- **DeepFace / Face Recognition**
- **TensorFlow**
- **MySQL**
- **dotenv**
- **Tkinter** (interfaz gráfica)

---

## 📋 Requisitos

- Python **3.10 **
- MySQL Server
- Cámara web funcional
- Sistema Operativo Windows / Linux
- Git (opcional)

---

## 📦 Instalación

### 1️⃣ Clonar el repositorio
```bash
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
