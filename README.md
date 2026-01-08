# 👤 Sistema de Reconocimiento Facial – Control de Asistencia

Sistema de **reconocimiento facial** desarrollado en **Python** que permite el **registro de usuarios** y la **toma de asistencia** mediante comparación facial, utilizando una base de datos **MySQL** para el almacenamiento de la información.

---

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
Clona el proyecto y accede
- git clone https://github.com/CRISTHIAN390/-Reconocimiento_facial.git
- cd ReconocimientoFacial

Crear entorno
python -m venv venv

Activa entorno
- venv\Scripts\activate

- pip install -r requirements.txt
Ejecuta
- python Login_Vision.py