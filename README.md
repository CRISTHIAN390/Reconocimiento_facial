# 👤 Sistema de Reconocimiento Facial – Control de Asistencia de Personal
Sistema de **reconocimiento facial** desarrollado en **Python** que permite al administrador gestionar el registro de trabajadores y realizar la toma de asistencia mediante comparación facial.
El sistema utiliza hasta 3 registros faciales por trabajador para mejorar la precisión y almacena la información en una base de datos **MySQL**.
--

## 🛠️ Tecnologías Utilizadas
- **Python 3.10**
- **DeepFace** (reconocimiento facial)
- **TensorFlow** (backend de DeepFace)
- **OpenCV (cv2)** (captura y procesamiento de imágenes)
- **MTCNN (Multi-task Cascaded Convolutional Networks)** (detección de rostros)
- **MySQL** (almacenamiento de datos)
- **python-dotenv** (gestión de variables de entorno)
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

```bash
1️⃣ Clonar el proyecto
- git clone https://github.com/CRISTHIAN390/-Reconocimiento_facial.git
- cd ReconocimientoFacial


2️⃣ Crear y activar el entorno virtual
- python -m venv venv
- venv\Scripts\activate
- pip install -r requirements.txt

3️⃣ Ejecutar la aplicación
- python Login_Vision.py

🧩 Generar el ejecutable
-Configura la conexión a la base de datos (local o cloud) y crea el usuario administrador con la contraseña encriptada.
-Define la ruta donde estarán los archivos del sistema.      PROJECT_DIR=""
-Instala PyInstaller: pip install pyinstaller
-Genera el ejecutable: pyinstaller --onefile --windowed --name="Sistema_Asistencia" --icon="icono.ico" launcher.py
-Entra a la carpeta dist, ejecuta Sistema_Asistencia.exe y listo.